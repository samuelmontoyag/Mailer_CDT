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
from models import events, posts, options, users

eventos = Blueprint('eventos', __name__)


def initialize_app(app):
    app.register_blueprint(eventos)


@eventos.route("/eventos", methods=['GET', 'POST'])
@login_required
def index():
    # users = Table('wp_options', db.metadata, autoload=True)
    # join = events.join(posts, events.c.post_id == posts.c.ID)
    # event_list = events.select().select_from(join).execute()
    event_list = []
    data = {
        'list': event_list
    }

    return render_template('eventos/list.html', title="Eventos", **data)


def get_event_data(id):
    join = events.join(posts,posts.c.ID ==  events.c.post_id )
    where = events.c.event_id == id
    event_data = events.select().where(where).select_from(join).execute()
    event_data = events_add_url(event_data)
    return event_data[0]


def events_add_url(events):
    # estructure = options.select().where(
    # options.c.option_name == 'permalink_structure')
    # baseUrl
    estructure = "/index.php/eventos/"
    base_url = "http://www-cdt-cl.devphp01.synaptic.cl"
    new_events = []
    for row in events:
        anno = unicode(row['event_date_created'])[0:4]
        mes = unicode(row['event_date_created'])[5:7]
        name = unicode(row['event_name'])
        url = estructure
        url = url.replace('%year%', anno)
        url = url.replace('%monthnum%', mes)
        url = url.replace('%postname%', name)
        url = base_url+url
        row = dict(row.items())
        row['url'] = url
        new_events.append(row)
    return new_events
