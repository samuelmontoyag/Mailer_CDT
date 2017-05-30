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
import csv
from time import time
from utils import get_mailchimp_api
import mailchimp


correos = Blueprint('correos', __name__)


def initialize_app(app):
    app.register_blueprint(correos)


@correos.route("/correos", methods=['GET', 'POST'])
@login_required
def index(message=None):
    try:
        m = get_mailchimp_api()
        lists = m.lists.list()

    except mailchimp.Error, e:
        return "Ha ocurrido un error al intentar conectar con mailchimp"
    data = {
        'lists': lists['data'],
        'message': message
    }
    return render_template('correos/list.html', title="NOMBRE", **data)


@correos.route('/correos/details/<id>', methods=['GET'])
@login_required
def list_details(id, message=None):
    try:
        m = get_mailchimp_api()
        lists = m.lists.list({'list_id': id})
        list = lists['data'][0]
        members = m.lists.members(id)['data']
        segments = m.lists.segments(id)
    except mailchimp.ListDoesNotExistError:
        return index("La lista no existe")
    except mailchimp.Error, e:
        return index("Ha ocurrido un error con mailchimp" + str(e))
    data = {
        'list': list,
        'members': members,
        'message': message,
        'segments': segments
    }

    return render_template('correos/details.html', **data)


@correos.route('/correos/add', methods=['POST'])
@login_required
def add():

    list_id = request.form['id']
    name = request.form['name']
    lastName = request.form['lastName']
    email = request.form['email']
    email = {'email': email}

    merge_vars = {'FNAME': name,
                  'LNAME': lastName
                  }
    try:
        m = get_mailchimp_api()
        status = m.lists.subscribe(list_id, email,
                                   merge_vars,
                                   'html',
                                   False, True,
                                   True, False)

        lists = m.lists.list({'list_id': list_id})
        list = lists['data'][0]
        members = m.lists.members(list_id)['data']
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp<br />"+str(e)

    data = {
        'list': list,
        'members': members
    }
    return render_template('correos/details.html', **data)


@correos.route('/correos/delete', methods=['POST'])
@login_required
def delete():
    euid = request.form['euid']
    email = request.form['emailDel']
    listId = request.form['listId']
    delete = 'delete' in request.form
    notify = 'notify' in request.form
    try:
        m = get_mailchimp_api()
        status = m.lists.unsubscribe(listId,
                                     {'email': email, 'euid': euid},
                                     delete, False, notify)
    except mailchimp.Error, e:
        return "Ha ocurrido un error con mailchimp<br />"+str(e)
    message = "<div class='alert alert-success'>"
    message += "Email eliminado correctamente"
    message += "</div>"
    return index(message)


@correos.route('/correos/import_preview', methods=['POST'])
@login_required
def import_preview():
    if request.method == 'POST':
        list_id = request.form['id']
        list_name = request.form['list_name']
        csv_file = request.files['emailsFile']
        data = csv_file.read()
        #genera el archivo temporal
        temp_filename = "file"+str(time())+".csv"
        temp_file = open("/tmp/"+temp_filename, 'w')
        temp_file.write(data)
        temp_file.close()

        temp_file = open("/tmp/"+temp_filename, 'r')

        reader = csv.reader(temp_file)
        columnNames = reader.next()
        lineas_totales = 0
        emails = []
        for row in reader:
            lineas_totales += 1
            if lineas_totales < 20:
                emails.append(row)

        temp_file.close()
        data = {
            'columnNames': columnNames,
            'totalLines': lineas_totales,
            'emails': emails,
            'list_id': list_id,
            'list_name': list_name,
            'emailsFile': temp_filename
        }
    return render_template("correos/import_preview.html", **data)


@correos.route('/correos/import', methods=['POST'])
@login_required
def import_csv():
    list_id = request.form['id']
    temp_filename = request.form['emailsFile']
    csv_file = open("/tmp/"+temp_filename, 'r')

    reader = csv.reader(csv_file)
    if 'columnTitle' in request.form:
        reader.next()

    column_headers = []
    column_index = []
    for column in request.form:
        if column.find("headerColumn") == 0:
            column_headers.append(request.form[column])
            column_index.append(column[-1:])

    email_index = int(column_index[column_headers.index("email")])
    name_index = None
    last_name_index = None
    if 'name' in column_headers:
        name_index = int(column_index[column_headers.index("name")])
    if 'lastName' in column_headers:
        last_name_index = int(column_index[column_headers.index("lastName")])
    batch_array = []
    for row in reader:
            email = {'email': row[email_index]}
            merge_vars = {}

            if name_index is not None:
                merge_vars['FNAME'] = row[name_index]
            if last_name_index is not None:
                merge_vars['LNAME'] = row[last_name_index]

            emailRow = {
                'email': email,
                'merge_vars': merge_vars
            }
            batch_array.append(emailRow)
    try:
        m = get_mailchimp_api()

        status = m.lists.batch_subscribe(list_id,
                                         batch_array,
                                         False, True, True)
        message = ""
        if status['add_count'] > 0:
            message += "<div class='alert alert-success'>"
            message += "se han importado <strong>" + str(status['add_count'])
            message += "</strong> emails.<br />"
            message += "</div>"
        if status['update_count'] > 0:
            message += "<div class='alert alert-success'>"
            message += "se han actualizado <strong>"
            message += str(status['update_count']) + "</strong> emails."
            message += "</div>"
        if status['error_count'] > 0:
            message += "<div class='alert alert-danger'>"
            message += "Se encontraron <strong>" + str(status['error_count'])
            message += "</strong> errores al importar."
            message += "<Table class='table'><tr>"
            message += "<th>codigo</th><th>email</th><th>error</th><tr>"
            for error in status["errors"]:
                message += "<tr>"
                message += "<td>"+str(error["code"])+"</td>"
                message += "<td>"+str(error["email"]["email"])+"</td>"
                message += "<td>"+str(error["error"])+"</td>"
                message += "</tr>"
            message += "</Table>"
            message += "</div>"

    except mailchimp.Error, e:
        print "ha ocurrido un error con mailchimp", e
    return list_details(list_id, message)
