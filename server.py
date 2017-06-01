# -*- coding: utf-8 -*-
from flask import Flask, render_template, session, request, make_response
from controllers import home, eventos, campagnas, correos, template, files
from models import init_db
from libs import auth
import os


def register_blueprints(app):
    auth.initialize_app(app)
    home.initialize_app(app)
    eventos.initialize_app(app)
    campagnas.initialize_app(app)
    correos.initialize_app(app)
    template.initialize_app(app)
    files.initialize_app(app)

app = Flask(__name__)

app.config.from_pyfile('config.ini')

init_db(app)
register_blueprints(app)

if __name__ == "__main__":
    app.run(port=4000)
