from flask import Flask
from flask_restx import Resource, Api

webapp = Flask(__name__)
api = Api(webapp)
