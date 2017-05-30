# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Table

db = None
events = None
posts = None
options = None
users = None


def init_db(app):
    global db, events, posts, options, users
    db = SQLAlchemy(app)
    db.metadata.bind = db.engine
    events = Table('wp_em_events', db.metadata, autoload=True)
    posts = Table('wp_posts', db.metadata, autoload=True)
    options = Table('wp_options', db.metadata, autoload=True)
    users = Table('mailing_users', db.metadata, autoload=True)

# class Events(db.Model):
#     __tablename__ = 'wp_em_events'
#     id = db.Column('ID', db.Integer, primary_key=True)


# class Posts(db.Model):
#     __tablename__ = 'wp_posts'
#     id = db.Column('ID', db.Integer, primary_key=True)
