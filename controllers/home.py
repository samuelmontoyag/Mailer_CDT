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
from utils import get_mailchimp_api
import json
home = Blueprint('home', __name__)


def initialize_app(app):
    app.register_blueprint(home)


@home.route("/", methods=['GET', 'POST'])
@login_required
def index():
    return render_template('index.html', title="Bienvenido")


@home.route("/statistics", methods=['GET', 'POST'])
@login_required
def statistics():
    m = get_mailchimp_api()
    data = {'mailing_count': m.campaigns.list(limit=0).get('total', 0),
            'template_count': len(m.templates.list().get('user')),
            'emails_list_count': m.lists.list(limit=0).get('total', 0)
            }
    return json.dumps(data)
