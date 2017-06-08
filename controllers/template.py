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
import mailchimp


template = Blueprint('template', __name__)


#mailchimp api key
def get_mailchimp_api():
    return mailchimp.Mailchimp('70459fe2c5d09c1f71a2d87d07bdffed-us3')


def initialize_app(app):
    app.register_blueprint(template)


@template.route("/plantillas/")
@login_required
def index(message=None):
    try:
        m = get_mailchimp_api()
        lists = m.templates.list()
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp", e
    data = {
        'lists': lists["user"],
        'message': message
    }
    return render_template("plantillas/list.html", **data)


@template.route("/plantillas/deleted", methods=['GET'])
@login_required
def eliminados(message=None):
    try:
        m = get_mailchimp_api()
        types = {}
        filter_templates = {'include_inactive': True, 'inactive_only': True}
        lists = m.templates.list(types, filter_templates)
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp", e
    data = {
        'lists': lists["user"],
        'message': message
    }
    return render_template("plantillas/list_eliminated.html", **data)


@template.route("/plantillas/create", methods=['GET'])
@login_required
def create():
    return render_template("plantillas/create.html")


@template.route("/plantillas/edit/<id>", methods=['GET'])
@login_required
def edit(id):
    try:
        id = int(id)
        m = get_mailchimp_api()
        types = {'user': True}
        templates = m.templates.list(types)
        source = m.templates.info(id)
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp", e
    except ValueError:
        message = "<div class='alert alert-danger'>"
        message += "el id de la plantilla no es valido"
        message += "</div>"
        return index(message)
    templates = templates['user']
    template_to_edit = None
    for template in templates:
        if template['id'] == id:
            template_to_edit = template
            break
    if template_to_edit is None:
        message = "<div class='alert alert-danger'>"
        message += "el id de la plantilla no se encuentra"
        message += "</div>"
        return index(message)
    template_to_edit['source'] = source
    data = {
        "template": template_to_edit
    }
    return render_template("plantillas/edit.html", **data)


@template.route("/plantillas/create", methods=['POST'])
@login_required
def create2():
    if request.method == 'POST':
        template_name = request.form['templateName']
        template_html = request.form['html']
        try:
            m = get_mailchimp_api()
            status = m.templates.add(template_name, template_html)
        except mailchimp.Error, e:
            return "Ha ocurrido un error con mailchimp", e
        flash("Plantilla agregada correctamente", "success")
    return redirect(url_for('.index'))


@template.route("/plantillas/update/<template_id>", methods=['POST'])
@login_required
def update(template_id):
    template_name = request.form['templateName']
    template_html = request.form['html']

    try:
        template_data = {'name': template_name,
                         'html': template_html
                         }
        m = get_mailchimp_api()
        status = m.templates.update(template_id, template_data)
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp", e
    message = "<div class='alert alert-success'>"
    message += "Plantilla actualizada correctamente"
    message += "</div>"
    return index(message)


@template.route("/plantillas/deactivate/<id>", methods=['GET'])
@login_required
def deactivate(id):
    template_id = id
    try:
        m = get_mailchimp_api()
        status = m.templates.delete(template_id)
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp", e
    message = "<div class='alert alert-success'>"
    message += "Plantilla desactivada correctamente"
    message += "</div>"
    return index(message)


@template.route("/plantillas/source/<id>", methods=['GET'])
@login_required
def source(id):
    try:
        id = int(id)
        m = get_mailchimp_api()
        source = m.templates.info(id)
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp", e
    return source['source']


@template.route("/plantillas/reactivate/<id>", methods=['GET'])
@login_required
def reactivate(id):
    try:
        m = get_mailchimp_api()
        status = m.templates.undel(id)
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp", e
    return index("<div class='alert alert-success'>Plantilla reactivada</div>")
