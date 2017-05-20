import sys
import os
import re

# Flask default JSON support (not stdlib)
#from flask import json

# for web queries
import requests

# image handling
from PIL import Image
from io import BytesIO

# file-type recognition
import magic

# local metadata extraction
from epub_meta import get_epub_metadata, get_epub_opf_xml, EPubException
from pdfrw import PdfReader

# scanning for paths
import glob

# END IMPORTS
#############

def main():
	test_path_1 = "epub/abriefhistory.epub"
	test_path_2 = "pdf/deathlyhallows.pdf"
	#print("TESTING LOCAL EXTRACTION...")
	#print(easy_scan("local", test_path_2))
	#print("TESTING REMOTE EXTRACTION...")
	#print(easy_scan("remote", easy_scan("local", test_path_2)))
	#print("TESTING COMPLETE EXTRACTION...")
	#print(easy_scan("complete", test_path_2))
	##print("TESTING FOLDER SCAN...")
	print(folder_scan("/storage"))
	

# takes a path to a folder and returns all PDF and ePub file paths inside
# WORKING examples: "storage", "storage/"
# NOT WORKING examples (gives empty list): "/storage", "/storage/"
def folder_scan(path):
	file_types = ('*.pdf', '*.epub')
	path_list = []
	for extension in file_types:
		path_list.extend(glob.glob(os.path.join(path, extension)))
	return path_list

def easy_scan(operator, aux):
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
	# 					title:
	# 					author:
	# 					identifier:
	# 					message:
	# 				remote:
	# 					title:
	# 					author:
	# 					description:
	# 					gbooksid:
	# 					thumbnail:
	if operator == "local":
		if type(aux) == type(""):
			return local_scanner(aux)
		else:
			return "error:not_a_string/path"
	elif operator == "remote":
		if type(aux) == type({}):
			return remote_scanner(aux)
		else:
			return "error:not_a_dict"
	elif operator == "complete":
		if type(aux) == type(""):
			local_dict = local_scanner(aux)
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
def local_scanner(path):
	# store the MIME type
	mimetype = magic.from_file(path, mime=True)
	# for ePub 2/3 files:
	if mimetype=="application/epub+zip":
		try:
			scan = get_epub_metadata(path)
			metadata = dict([("type", "epub"), ("title", scan.title), ("author", scan.authors), ("identifier", scan.identifiers), ("message", "success")])
		except EPubException as e:
			metadata = "Sorry, that is not an ePub file"
	# for PDF files:		
	elif mimetype=="application/pdf":
		scan = PdfReader(path).Info
		metadata = dict([("type", "pdf"), ("title", scan.Title.decode()), ("author", scan.Author.decode()), ("identifier", ""), ("message", "success")])
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

	# thumbnail is trickier: we need a large image and then store it as binary (needs work!)
	zoom_param = {"zoom" : "0"}
	thumbnail_link = search_data["items"][0]["volumeInfo"]["imageLinks"]["thumbnail"]
	thumbnail = Image.open(BytesIO(requests.get(thumbnail_link, zoom_param).content))

	# return the final metadata
	metadata = dict([("title", title), ("author", author), ("description", description), ("gbooksid", gbooksid), ("thumbnail", thumbnail)])
	return metadata

# takes in a local_scanner dict and a remote_scanner dict and combines
def meta_combine(local_dict, remote_dict):
	return dict([("local", local_dict), ("remote", remote_dict)])

	

if __name__ == "__main__":
    main()
