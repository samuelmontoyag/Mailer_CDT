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
    url_for,
    send_from_directory
)
from flask_login import login_required, current_user
from sqlalchemy import Table
from utils import get_mailchimp_api
from werkzeug import secure_filename
from eventos import get_event_data
import os
import json
import datetime
from bson import json_util, ObjectId
files = Blueprint('files', __name__)
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc',
                          'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'])


def toJson(r):
    return json.dumps(r, default=json_util.default)


def initialize_app(app):
    app.register_blueprint(files)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@files.route("/files/upload", methods=["POST", "GET"])
def upload_file():
    if request.method == 'POST':
        file = request.files["upload"]
        if file and allowed_file(file.filename.lower()):
            now = datetime.datetime.now()
            year = now.year
            month = now.month
            extra_path = str(year)+"/"+str(month)+"/"
            filename = secure_filename(file.filename)
            path = os.path.join(current_app.config["UPLOAD_FOLDER"], extra_path)
            if not os.path.exists(path):
                os.makedirs(path)
            if os.path.exists(os.path.join(path, filename)):
                ##comprobar que el hash no exista
                add = 1
                while os.path.exists(os.path.join(path, str(add)+filename)):
                    add = add + 1
                filename = str(add)+filename
            file.save(os.path.join(path, filename))
            ckEditorFuncNum = request.args.get("CKEditorFuncNum", "0")

        url = '<script type="text/javascript">window.parent.CKEDITOR\
              .tools.callFunction(%s,"http://%s%s");</script>' % \
              (ckEditorFuncNum,
               request.host,
               url_for('files.uploaded_file',
                       filename=filename, year=year,
                       month=month))
        return url


@files.route('/files/<year>/<month>/<filename>')
def uploaded_file(year, month, filename):
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], year, month)
    return send_from_directory(path,
                               filename)


@files.route('/files/<filename>')
def uploaded_file_old(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"],
                               filename)


@files.route('/files/list/json')
def files_list_json():
    json = []
    try:
        lst = os.listdir(current_app.config["UPLOAD_FOLDER"])
        lst_walker = os.walk(current_app.config["UPLOAD_FOLDER"])
    except OSError:
        pass
    else:
        for line in lst_walker:
            if len(line[2]) > 0:
                for file in line[2]:
                    index_month = line[0].rindex("/")
                    index_year = line[0].rindex("/", 0, index_month)
                    month = line[0][index_month+1:]
                    year = line[0][index_year+1:index_month]
                    json.append({'image': '/files/'+year+'/'+month+'/'+file})
    return toJson(json)
