# -*- coding: utf-8 -*-
from flask import (
    Blueprint,
    current_app,
    Response,
    abort,
    jsonify,
    request,
    session,
    redirect,
    flash,
    render_template,
    url_for
)
from flask_login import login_required, current_user
from sqlalchemy import Table

home = Blueprint('home', __name__)


def initialize_app(app):
    app.register_blueprint(home)


@home.route("/", methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', title="Bienvenido")
