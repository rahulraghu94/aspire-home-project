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
import wikipedia

app = Flask(__name__)

@app.route("/")
def main_page():
	return render_template('home.html')

@app.route("/account")
def my_account():
	return render_template('account.html')

if __name__ == '__main__':
	app.debug = True
	handler = RotatingFileHandler('wine-catalog.log', maxBytes=10000, backupCount=1)
	handler.setLevel(logging.INFO)
	formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
	handler.setFormatter(formatter)
	app.logger.addHandler(handler)
	app.run(host = '0.0.0.0', port = 8000)
