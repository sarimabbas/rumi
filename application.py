import os
import re
from flask import Flask, jsonify, render_template, request, url_for

# import mongodb tools
from pymongo import MongoClient

# import helpers
from helpers import *

# configure application
app = Flask(__name__)
app.config['DEBUG'] = True

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

@app.route("/")
def index():
	test_path_1 = "epub/abriefhistory.epub"
	test_post = easy_scan("complete", test_path_1)
	test_scan = folder_scan("storage")

	print(test_post)
	print(test_scan)

	#books_insertion_id = books_table.insert_one(test_post).inserted_id
	#print(books_insertion_id)



	return "render_template"





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