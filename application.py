import os
import datetime # perhaps for inserting a timestamp into mongo documents
import pprint # for testing

# import web framework
from flask import Flask, jsonify, render_template, request, url_for
from flask_session import Session
from flask_jsglue import JSGlue
from tempfile import gettempdir

# import helpers
from helpers import *

# import mongodb tools
from pymongo import MongoClient

# END IMPORTS
#############

# configure application
app = Flask(__name__)
JSGlue(app)
#app.config['DEBUG'] = True

# mongodb database setup
client = MongoClient("mongodb://sarimabbas:#Eg974is@sarim-test-shard-00-00-7p32o.mongodb.net:27017,sarim-test-shard-00-01-7p32o.mongodb.net:27017,sarim-test-shard-00-02-7p32o.mongodb.net:27017/?ssl=true&replicaSet=sarim-test-shard-0&authSource=admin")
db = client["rumi"]

# the tables/collections needed:
users_table = db["users"] # for users: username, email, password etc
groups_table = db["groups"] # for user permissions: admin, viewer etc
books_table = db["books"] # for books

# ensure responses aren't cached
if app.config["DEBUG"]:
	@app.after_request
	def after_request(response):
		response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
		response.headers["Expires"] = 0
		response.headers["Pragma"] = "no-cache"
		return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# END CONFIG
############

@app.route("/")
def index():

	hack_script = "<script type='text/javascript'>$('.download').on('click', function() { var download_id = $(this).data('book-id'); console.log(download_id); });</script>"
	
	test_path_1 = "storage/abriefhistory.epub"
	test_path_2 = "storage/deathlyhallows.pdf"
	#test_post = easy_scanner("complete", test_path_1)

	#print(test_post)

	#books_insertion_id = books_table.insert_one(test_post).inserted_id
	#print(books_insertion_id)
	
	books = book_retrieve()
	return render_template("index.html", books=books, script=hack_script)


# testing to do:
# 	1. what happens when 0 books are found
# 	2. when 1 book is found?
def book_retrieve(operator={}):
	response = list(books_table.find(operator)) # convert pymongo cursor to list
	return response


	#print(type(response))
	#if type(response) == type({}):
	#	return [response]
	#elif type(response) == type([]):
	#	return response


# uses mongodb object id
#@app.route("/download", methods=["POST"])
#@login_required
#def file_retrieve(id):
	# search mongodb by id
	# retrieve json object
	# check the dict -> local -> location
	# if location -> dropbox
	# 	instantiate and connect to dropbox
	# 	use location -> dropbox -> path to check file
	# 	if file is present:
	# 		create a download link and open in new tab
	# if location -> local
	# 	download the path


# takes a list of file paths, compares them to the database, 
# and determines which ones need to be imported 
# (this is better than retrieving the metadata and merging later)
# probably need this at the time of importing files
# def library_merge

# checks a record's file path to see if the file actually exists. If not, it deletes the record
# probably need this at the time of downloading/retrieving a file
# def record_prune





## initialise the database with the required tables etc
# def init_db():

### killswitch
def shutdown_server():
	func = request.environ.get('werkzeug.server.shutdown')
	if func is None:
		raise RuntimeError('Not running with the Werkzeug Server')
	func()

@app.route('/shutdown', methods=['GET'])
def shutdown():
	shutdown_server()
	return 'Server shutting down...'