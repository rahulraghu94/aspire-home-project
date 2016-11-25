#!/usr/bin/python2.7

from flask import Flask, render_template, request, url_for, redirect, flash, jsonify, abort, g, make_response, session as login_session
import random, string
#from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError, AccessTokenCredentials
import httplib2
import json
import requests
from functools import update_wrapper
import time
import pg
import logging
from logging.handlers import RotatingFileHandler
import urlparse

url = "postgres://xfckxhvrnurzab:grWHL5-NDkLx60q3ha1sW-gvHt@ec2-174-129-3-207.compute-1.amazonaws.com:5432/dfjp7s1fia74dc"

url = urlparse.urlparse(url)
db = pg.DB(dbname = url.path[1:], host = url.hostname, port = url.port, user = url.username, passwd = url.password)

app = Flask(__name__)

app.secret_key = "super_secret_key"

# Variable to hold Google OAuth ID
CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

###############################################################################
# Login
###############################################################################
def getUserId(email):
	# Extracts the USER_ID from Postgres, given a users email
	try:
		db.query('end')
		db.query('begin')
		
		query = ("select * from users where email = '{}'").format(email)
		
		user = db.query(query)
		user = user.dictresult()
		
		db.query('end')
		
		return user[0]['id']
	except:
		return None

def getUserInfo(user_id):
	# Given a USER_ID extract all information about that user.
	# Include name, picture, text data, email etc
	db.query('end')
	db.query('begin')
	user = ("select * from users where id = '{}'").format(user_id)
	user = user.dictresult()
	user = user[0]
	db.query('end')
	return user

def createUser(login_session):
	# Accept a flask login session object and create a new user
	# If sucha user already exists, relog and move on
	t = time.asctime()
	new_user = {'name' : login_session['username'], 'email' : login_session['email'], 'picture' : login_session['picture'], 'time' : t}

	db.query('end')
	db.query('begin')
	
	db.insert('users', new_user)
	
	query = ("select * from users where email = '{}'").format(login_session['email'])
	
	user = db.query(query)
	user = user.dictresult()
	user = user[0]
	
	# Log a new user
	app.logger.info("Created User: ID = ", user['id'])
	
	db.query('end')
	return user['id']

@app.route('/gconnect', methods = ['POST'])
# /gconnect gets called from the /login page.
# Called by the JavaScript module
def gconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter'), 401)
		response.headers['Content-tyoe'] = 'application/json'
		return response

	code = request.data

	# Obtain Credentials from Google
	try:
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)

	except FlowExchangeError:
		response = make_response(json.dumps('Auth Code Upgradation Failure'), 401)
		response.headers['Content-tyoe'] = 'application/json'
		return response

	# Extract Access token from credentials
	access_token = credentials.access_token
	url = 'https://www.googleapis.com/oauth2/v2/tokeninfo?access_token='
	url = url + access_token
	h = httplib2.Http()

	result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))

	# If error in extracting credentials, report error
	if result.get('error') is not None:
		response - make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-tyoe'] = 'application/json'

	# Extract G+ ID from credentials
	gplus_id = credentials.id_token['sub']

	# If credentials and access tokens don't match, throw error
	if result['user_id'] != gplus_id:
		response = make_response(json.dumps("Token ID mismatch"), 401)
		response.headers['Content-tyoe'] = 'application/json'
		return response

	if result['issued_to'] != CLIENT_ID:
		response = make_response(json.dumps('Client ID mismatch'), 401)
		response.headers['Content-tyoe'] = 'application/json'
		return response

	# Check if the user is already logged in by peeking at login_session
	# If so, return success
	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')

	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('User is already logged in'), 200)
		response.headers['Content-tyoe'] = 'application/json'

	# Store valid credentials in local Flask's loggin_session
	login_session['credentials'] = credentials.access_token
	credentials = AccessTokenCredentials(login_session['credentials'], 'user-agent-value')
	login_session['gplus_id'] = gplus_id

	# Extract user info from obtained credentials
	userinfo_url = ("https://www.googleapis.com/oauth2/v2/userinfo")
	params = {'access_token' : credentials.access_token, 'alt' : 'json'}

	answer = requests.get(userinfo_url, params=params)
	data = json.loads(answer.text)

	# Parse obtained information in JSON format and store
	login_session['username'] = data["name"]
	login_session['picture'] = data["picture"]
	login_session['email'] = data["link"]

	# Check if user had logged in before and is simply revisiting
	user_id = getUserId(login_session['email'])

	# If user_id does not exists in USER table, create a new user
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id

	# Log new user connects
	app.logger.info("New User Connected: ID = {}".format(user_id))

	return "Done: 200"

@app.route("/gdisconnect")
def gdisconnect():
	# Get currant users credentials from login_session
	credentials = login_session['credentials']

	# If it doesn't exist, user has already logged out
	if credentials is None:
		response = make_response(json.dumps('The currant user is not logged in'), 401)
		response.headers['Content-tyoe'] = 'application/json'
		return response

	# Google SPI to revoke access
	access_token = credentials
	url = "https://accounts.google.com/o/oauth2/revoke?token="
	url += access_token

	h = httplib2.Http()
	result = h.request(url, 'GET')[0]

	# Update login_session to show that user is not logged in
	if result['status'] == '200':
		del login_session['username']
		del login_session['picture']
		del login_session['email']

		response = make_response(json.dumps('Successfully disconnected!'), 200)
		response.headers['Content-tyoe'] = 'application/json'

		app.logger.info("User Disconnected: ID = {}".format(login_session['user_id']))

		return redirect('/')

	# In case Revoke API didn't work
	else:
		response = make_response(json.dumps("Something went wrong... Try again"), 400)
		response.headers['Content-tyoe'] = 'application/json'
		return response
	return 'ok'

###############################################################################
# This i back end for main page
# localhost:5000 as well as localhost.com will route to the same login.html

# Page is done in Boot Strap
###############################################################################
@app.route("/")
@app.route('/login')
def login():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)

###############################################################################
# Users account page.
# Redirected from the login function
###############################################################################
@app.route("/account", methods=['GET', 'POST'])
def account():
	if 'username' not in login_session:
		return redirect('/login')

	db.query('end')
	db.query('begin')
	user_id = getUserId(login_session['email'])

	query = ("select * from users where id = '{}'").format(user_id)
	user = db.query(query)
	user = user.dictresult()
	user_name = user[0]['name']

	user_data = user[0]['data']

	# If information received from user, do an update
	if request.method == 'POST':
		t = time.asctime()
		user[0]['data'] = request.form['data']
		user[0]['time'] = t

		db.update('users', user[0])
		db.query('end')

		app.logger.info("Data updated by user with ID: {} at time: {}".format(user_id, t))

		return redirect('/account')

	# Else, render the users account page
	else:
		return render_template('account.html', name = user_name, data = user_data, time = user[0]['time'])

# For error handeling and logging
@app.errorhandler(500)
def internal_error(exception):
	app.logger.error(exception)

if __name__ == '__main__':
	app.debug = True

	# Code to enable logging.
	# Helpful when we need to track user actions
	handler = RotatingFileHandler('wine-catalog.log', maxBytes=10000, backupCount=1)
	handler.setLevel(logging.INFO)
	formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
	handler.setFormatter(formatter)
	app.logger.addHandler(handler)
	
	# Starting the app on port 5000
	#app.run(host = '0.0.0.0', port = 5000)
