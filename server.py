# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, session, request, \
    make_response
import mailchimp

def register_blueprints(app):
    import auth
    auth.initialize_app(app)
    import home
    home.initialize_app(app)
    import eventos
    eventos.initialize_app(app)
    import campagnas
    campagnas.initialize_app(app)
    import correos
    correos.initialize_app(app)
    import template
    template.initialize_app(app)
    import files
    files.initialize_app(app)

app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
config = os.path.join(app.root_path, 'config.ini')
if not os.path.exists(config):
    raise Exception("Falta el archivo config.ini")
app.config.from_pyfile(config)

from models import init_db
init_db(app)
register_blueprints(app)

if __name__ == "__main__":
    app.run(port=4000)
