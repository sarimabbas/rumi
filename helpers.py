# BEGIN IMPORTS
###############
import sys
import os
import re

# Flask default JSON support (not stdlib)
#from flask import json

# for web queries
import requests

# import cloud storage tools
import dropbox

# image handling
from PIL import Image
from io import BytesIO
import base64

# file-type recognition
import magic

# local metadata extraction
from epub_meta import get_epub_metadata, get_epub_opf_xml, EPubException
from pdfrw import PdfReader

# scanning for paths
import glob

# END IMPORTS
#############

# TEST AREA
###########
def main():
	test_path_1 = "storage/abriefhistory.epub"
	test_path_2 = "storage/deathlyhallows.pdf"
	#print("TESTING LOCAL EXTRACTION...")
	#print(easy_scan("local", test_path_2))
	#print("TESTING REMOTE EXTRACTION...")
	#print(easy_scan("remote", easy_scan("local", test_path_2)))
	#print("TESTING COMPLETE EXTRACTION...")
	#print(easy_scan("complete", test_path_2))
	##print("TESTING FOLDER SCAN...")
	#access_token = "KJr-yI6FtLsAAAAAAAAEUZivoiqVotmYXynIHhQ35JwdrTTFswiTOWoKy5Slezz9"
	#dropbox_scan(access_token, "/books/calibre/stephen king")

# BEGIN SCAN FUNCTIONS
######################
# linguistics: scans are for folders, scanners are for files

# let's make it support multiple storage_dir in the future, not now!
def dropbox_scan(access_token, storage_dir):
	dbx = dropbox.Dropbox(access_token)
	for entry in dbx.files_list_folder(storage_dir, recursive=True).entries:
		extension = os.path.splitext(entry.path_display)[1] # split the returned file path
		if (extension == ".epub") or (extension == ".pdf"):
			tmp_dl = dbx.files_download_to_file("tmp/" + entry.name, entry.path_display) # download file
			# now scan 'em
			print(easy_scanner("complete", "tmp/" + entry.name, {"dropbox":entry.path_display})) # test
			# store the records
			# delete the files

# takes a path to a folder and returns all PDF and ePub file paths inside
# WORKING examples: "storage", "storage/"
# NOT WORKING examples (gives empty list): "/storage", "/storage/"
def folder_scan(path):
	file_types = ('*.pdf', '*.epub')
	path_list = []
	for extension in file_types:
		path_list.extend(glob.glob(os.path.join(path, extension)))
	return path_list

# END SCAN FUNCTIONS
####################

# BEGIN SCANNER FUNCTIONS
#########################
# linguistics: scans are for folders, scanners are for files

def easy_scanner(operator, aux, location="local"):
	# operators
	# 	local: does local metadata extraction
	# 		aux: must be set to file path
	# 	remote: does remote metadata extraction
	# 		aux: must be set to local_dict
	# 	complete: does local followed by remote
	# 		aux: must be set to file path
	# 		returns a dict:
	# 			dict:
	# 				local:
	# 					type: epub/pdf/error
	# 					path:
	# 					title:
	# 					author:
	# 					identifier:
	# 					message:
	# 					location: local/dropbox/googledrive/
	# 				remote:
	# 					title:
	# 					author:
	# 					description:
	# 					gbooksid:
	# 					thumbnail:
	# location
	# 	local: in this context means stored on the file system (default)
	# 	dropbox: stored on dropbox
	# 	googledrive: stored on google drive
	if operator == "local":
		if type(aux) == type(""):
			return local_scanner(aux, location)
		else:
			return "error:not_a_string/path"
	elif operator == "remote":
		if type(aux) == type({}):
			return remote_scanner(aux)
		else:
			return "error:not_a_dict"
	elif operator == "complete":
		if type(aux) == type(""):
			local_dict = local_scanner(aux, location)
			remote_dict = remote_scanner(local_dict)
			return meta_combine(local_dict, remote_dict)
		else:
			return "error:not_a_string/path"
	else:
		return "error:not_an_operator"


# takes in a path to a document and returns its local metadata
# dict:
# 	type: epub/pdf/error
# 	title:
# 	author:
# 	identifier:
# 	message:
def local_scanner(path, location="local"):
	# store the MIME type
	mimetype = magic.from_file(path, mime=True)
	# for ePub 2/3 files:
	if (mimetype=="application/epub+zip") or ((mimetype=="application/zip") and (path.endswith(".epub"))):
		try:
			scan = get_epub_metadata(path)
			metadata = dict([("type", "epub"), ("path", path), ("title", scan.title), ("author", scan.authors), ("identifier", scan.identifiers), ("location", location)])
		except EPubException as e:
			metadata = "Sorry, that is not an ePub file"
	# for PDF files:		
	elif mimetype=="application/pdf":
		scan = PdfReader(path).Info
		metadata = dict([("type", "pdf"), ("path", path), ("title", scan.Title.decode()), ("author", scan.Author.decode()), ("identifier", ""), ("location", location)])
	# don't accept anything else
	else:
		metadata = {"type":"error", "message":"Sorry, ePubs and PDFs only!"}
	return metadata

# takes in a dict created by local_scanner
# uses the information by doing a Google Books lookup
# returns a dict
# dict:
# 	title:
# 	author:
# 	description:
# 	gbooksid:
# 	thumbnail:
def remote_scanner(local_dict):
	# if the local_dict is not from an ePub or PDF:
	if local_dict["type"] == "error":
		return dict([("title", ""), ("author", ""), ("description", ""), ("gbooksid", ""), ("thumbnail", "")])
	
	# needed variables for remote lookup
	gbooks_URI = "https://www.googleapis.com/books/v1/volumes"
	search_params = dict([("q", local_dict["title"])])

	# perform lookup
	r = requests.get(gbooks_URI, params=search_params)
	search_data = r.json()

	# construct and return the remote_dict
	title = search_data["items"][0]["volumeInfo"]["title"]
	author = search_data["items"][0]["volumeInfo"]["authors"]
	description = search_data["items"][0]["volumeInfo"]["description"]
	gbooksid = search_data["items"][0]["id"]

	# thumbnail is trickier: we need a large image and then store it as a data string
	zoom_param = {"zoom" : "0"} # for getting a good image from Google Books API
	thumbnail_link = search_data["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]
	thumbnail_response = requests.get(thumbnail_link, zoom_param)
	thumbnail = ["data:", thumbnail_response.headers["Content-Type"], ";", "base64,", str(base64.b64encode(thumbnail_response.content).decode("utf-8"))]
	print(type(thumbnail))

	# return the final metadata
	metadata = dict([("title", title), ("author", author), ("description", description), ("gbooksid", gbooksid), ("thumbnail", thumbnail)])
	return metadata

# takes in a local_scanner dict and a remote_scanner dict and combines
# needed for easy_scanner("complete")
def meta_combine(local_dict, remote_dict):
	return dict([("local", local_dict), ("remote", remote_dict)])

# END SCANNER FUNCTIONS
#######################
	

if __name__ == "__main__":
    main()
