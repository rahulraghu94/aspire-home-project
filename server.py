#!/usr/bin/python2.7

from flask import Flask, render_template, request, url_for, redirect, flash, jsonify, abort, g, make_response, session as login_session
import random, string
#from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError, AccessTokenCredentials
import httplib2
import json
import requests
from redis import Redis
from functools import update_wrapper
import time
import pg
import logging
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse
import time

db = pg.DB(dbname = "home-project-database", user = "rahul")
#url = "postgres://yxdfmijogkeoqu:nJHb0aelUdgoS4vAQAdR35qIRg@ec2-23-21-164-237.compute-1.amazonaws.com:5432/d3rcfql3m4pa15"

#url = urlparse(url)
#db = pg.DB(dbname = "d3rcfql3m4pa15", host = url.hostname, port = url.port, user = url.username, passwd = url.password)

app = Flask(__name__)

app.secret_key = "super_secret_key"

CLIENT_ID = json.loads(open('client_secrets.json', 'r').read())['web']['client_id']

print (CLIENT_ID)

###############################################################################
# Login
###############################################################################
def getUserId(email):
	try:
		db.query('begin')
		query = ("select * from users where email = '{}'").format(email)
		user = db.query(query)
		user = user.dictresult()
		db.query('end')
		return user[0]['id']
	except:
		return None

def getUserInfo(user_id):
	db.query('begin')
	user = ("select * from users where id = '{}'").format(user_id)
	user = user.dictresult()
	user = user[0]
	db.query('end')
	return user

def createUser(login_session):
	t = time.asctime()
	new_user = {'name' : login_session['username'], 'email' : login_session['email'], 'picture' : login_session['picture'], 'time' : t}

	db.query('begin')
	db.insert('users', new_user)
	query = ("select * from users where email = '{}'").format(login_session['email'])
	user = db.query(query)
	user = user.dictresult()
	user = user[0]
	app.logger.info("Created User: ID = ", user['id'])
	db.query('end')
	return user['id']

@app.route('/gconnect', methods = ['POST'])
def gconnect():
	if request.args.get('state') != login_session['state']:
		response = make_response(json.dumps('Invalid state parameter you mofofs'), 401)
		response.headers['Content-tyoe'] = 'application/json'
		return response

	code = request.data

	try:
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps('Auth Code Upgradation Failure'), 401)
		response.headers['Content-tyoe'] = 'application/json'
		return response

	access_token = credentials.access_token
	url = 'https://www.googleapis.com/oauth2/v2/tokeninfo?access_token='
	url = url + access_token
	h = httplib2.Http()

	result = json.loads(h.request(url, 'GET')[1].decode('utf-8'))

	if result.get('error') is not None:
		response - make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-tyoe'] = 'application/json'

	gplus_id = credentials.id_token['sub']

	if result['user_id'] != gplus_id:
		response = make_response(json.dumps("Token ID mismatch"), 401)
		response.headers['Content-tyoe'] = 'application/json'
		return response

	if result['issued_to'] != CLIENT_ID:
		response = make_response(json.dumps('Client ID mismatch'), 401)
		response.headers['Content-tyoe'] = 'application/json'
		return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')

	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('User is already logged in'), 200)
		response.headers['Content-tyoe'] = 'application/json'

	login_session['credentials'] = credentials.access_token
	credentials = AccessTokenCredentials(login_session['credentials'], 'user-agent-value')
	login_session['gplus_id'] = gplus_id

	userinfo_url = ("https://www.googleapis.com/oauth2/v2/userinfo")
	params = {'access_token' : credentials.access_token, 'alt' : 'json'}

	answer = requests.get(userinfo_url, params=params)
	data = json.loads(answer.text)

	login_session['username'] = data["name"]
	login_session['picture'] = data["picture"]
	login_session['email'] = data["link"]

	user_id = getUserId(login_session['email'])

	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id

	app.logger.info("New User Connected: ID = ", user_id)

	return "Done: 200"

@app.route("/gdisconnect")
def gdisconnect():
	credentials = login_session['credentials']
	if credentials is None:
		response = make_response(json.dumps('The currant user is not logged in'), 401)
		response.headers['Content-tyoe'] = 'application/json'
		return response

	access_token = credentials
	url = "https://accounts.google.com/o/oauth2/revoke?token="
	url += access_token

	h = httplib2.Http()
	result = h.request(url, 'GET')[0]

	if result['status'] == '200':
		del login_session['username']
		del login_session['picture']
		del login_session['email']

		response = make_response(json.dumps('Successfully disconnected!'), 200)
		response.headers['Content-tyoe'] = 'application/json'

		app.logger.info("User Disconnected: ID = ", login_session['user_id'])

		return redirect('/')

	else:
		response = make_response(json.dumps("Something went wrong... Try again"), 400)
		response.headers['Content-tyoe'] = 'application/json'
		return response
	return 'ok'

@app.route("/")
@app.route('/login')
def login():
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in range(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)

@app.route("/account", methods=['GET', 'POST'])
def account():
	if 'username' not in login_session:
		return redirect('/login')

	db.query('begin')
	user_id = getUserId(login_session['email'])

	query = ("select * from users where id = '{}'").format(user_id)
	user = db.query(query)
	user = user.dictresult()
	user_name = user[0]['name']

	user_data = user[0]['data']

	if request.method == 'POST':
		t = time.asctime()
		user[0]['data'] = request.form['data']
		user[0]['time'] = t

		db.update('users', user[0])
		db.query('end')

		return redirect('/account')

	else:
		return render_template('account.html', name = user_name, data = user_data, time = user[0]['time'])

@app.errorhandler(500)
def internal_error(exception):
	app.logger.error(exception)

if __name__ == '__main__':
	app.debug = True
	handler = RotatingFileHandler('wine-catalog.log', maxBytes=10000, backupCount=1)
	handler.setLevel(logging.INFO)
	formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
	handler.setFormatter(formatter)
	app.logger.addHandler(handler)
	app.run(host = '0.0.0.0', port = 5000)
