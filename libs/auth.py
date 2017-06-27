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
from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
from flask_login import LoginManager
from bson import ObjectId
from sqlalchemy import Table
from models import events, posts, options, users
from bson.errors import InvalidId
import crypt
from models import users
auth = Blueprint('auth', __name__)


class User(object):

    def is_active(self):
        return True

    def get_id(self, as_string=True):
        if as_string:
            return str(self.get_id(False))
        return self.doc.user_id

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def get(self, attr, or_default=None):
        return self.doc[attr]

    @classmethod
    def get_object_id(cls, str):
        try:
            return ObjectId(str)
        except InvalidId:
            return None

    @classmethod
    def get_by_username(cls, user_id):

        doc = users.select().where(users.c.user_login == user_id).execute()
        doc = doc.first()
        if not doc:
            return None
        user = cls()
        user.doc = doc
        return user

    @classmethod
    def get_by_id(cls, user_id):

        doc = users.select().where(users.c.user_id == user_id).execute()
        doc = doc.first()
        if not doc:
            return None
        user = cls()
        user.doc = doc
        return user

    @classmethod
    def get_and_check_user(cls, username, password):
        user = cls.get_by_username(username)
        password_salt = current_app.config["PASSWORD_SALT"]

        if user and user.doc.user_pass == crypt.crypt(password, password_salt):
            return user
        return None

    @classmethod
    def set_password(cls, username, newPassword):
        password_salt = current_app.config["PASSWORD_SALT"]
        new_password_salt = crypt.crypt(newPassword, password_salt)
        update = users.update().where(users.c.user_login == username).\
                                values(user_pass=new_password_salt).execute()


def initialize_app(app):
    login_manager = LoginManager()

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)

    @app.errorhandler(401)
    def custom_401(error):
        flash(u'No está autorizado para ver esta página.', "error")
        return redirect(url_for('auth.login'))

    login_manager.init_app(app)
    app.register_blueprint(auth)


@auth.route("/auth/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.get_and_check_user(request.form['username'],
                                       request.form['password'])
        if user:
            login_user(user)
            flash("Login as, %s" % user.get("user_name"), "success")
            return redirect(request.args.get("next") or url_for("home.index"))
        flash(u'Nombre de usuario y/o contraseña incorrecta.', "error")
    if current_user.is_authenticated():
        return redirect(url_for("home.index"))
    return render_template('login.html')


@auth.route("/auth/logout", methods=['GET', 'POST'])
def logout():
    logout_user()
    flash(u'Sesion cerrada correctamente.', "success")
    return redirect(url_for('auth.login'))


@auth.route("/auth/profile", methods=['GET', 'POST'])
@login_required
def profile():
    return render_template('auth/profile.html')


@auth.route("/auth/change_passwd", methods=['GET', 'POST'])
@login_required
def change_passwd():
    if request.method == 'POST':
        user = User.get_and_check_user(current_user.doc.user_login,
                                       request.form['oldPassword'])
        if user:
            new_passwd = request.form["newpassword"]
            User.set_password(current_user.doc.user_login, new_passwd)
            flash(u"Su contraseña ha sido cambiada, exitosamente", "success")
        else:
            flash(u"La contraseña actual no es correcta", "error")
    return render_template('auth/passwd.html')


@auth.route("/auth/users", methods=['GET', 'POST'])
@login_required
def list_users():
    usuarios = users.select().execute()
    data = {
        'users': usuarios
    }
    return render_template('auth/users.html', **data)


@auth.route("/auth/user/new/", methods=['GET', 'POST'])
@auth.route("/auth/user/new/<user_id>", methods=['GET', 'POST'])
@login_required
def new_user(user_id=None):
    data = dict()
    if user_id:
        user = User.get_by_id(user_id)
        if user is None:
            flash("No se ha encontrado el usuario", "error")
        else:
            data = {
                'user_name': user.get("user_name"),
                'user_login': user.get("user_login"),
                'user_role': user.get("user_role"),
                'editando': True
            }
    if request.method == 'POST':
        data = {
            'user_name': request.form.get("user_name"),
            'user_login': request.form.get("user_login"),
            'user_role': request.form.get("user_role")
        }
        if user_id is None:
            if User.get_by_username(data.get("user_login")) is None:
                new = users.insert(data).execute()
                flash("Usuario agregado correctamente", "success")
            else:
                flash("Este usuario ya existe", "error")
        else:
            users.update().where(users.c.user_id == user_id).\
                           values({'user_login': data.get("user_login"),
                                   'user_name': data.get("user_name"),
                                   'user_role': data.get("user_role")
                                   }
                                  ).execute()
            data['editando'] = True
            flash("Usuario actualizado correctamente", "success")
        if len(request.form.get("user_pass")) > 0 and data.get("editando"):
            User.set_password(data.get("user_login"),
                              request.form.get("user_pass"))
            flash(u"Contraseña actualizada correctamente", "success")

    return render_template('auth/create_user.html', **data)


@auth.route("/auth/user/remove/", methods=['POST'])
@login_required
def remove_user():
    user_id = request.form.get("id_usuario")
    if user_id:
        users.delete().where(users.c.user_id == user_id).execute()
        flash("Usuario eliminado correctamente", 'success')
    return redirect(url_for('auth.list_users'))
