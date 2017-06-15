# -*- coding: utf-8 -*-
import os
import math
import pymongo
from datetime import datetime
from wtforms import fields
from bson import ObjectId
from flask import current_app
from flask.ext.admin import Admin
from flask.ext.pymongo import PyMongo
from flask.ext.wtf import form
from flask.ext.admin.contrib.pymongo import ModelView

class UserForm(form.Form):
    name = fields.TextField('Name')
    email = fields.TextField('Email')
    username = fields.TextField('Username')
    password = fields.TextField('Password')


class UserView(ModelView):
    column_list = ('username', 'name', 'email')
    column_sortable_list = ('username', 'name', 'email')
    form = UserForm


def get_db(app):
    from db import db
    return db


def initialize_app(app):
    admin_manager = Admin(app, 'Administrator')
    admin_manager.add_view(UserView(get_db(app).users, 'Users'))
