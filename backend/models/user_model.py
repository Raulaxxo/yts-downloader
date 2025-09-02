from flask_login import UserMixin
from datetime import datetime
import uuid

class User(UserMixin):
    id = None
    username = None
    password = None
    created_at = None
    downloads = None
    
    @staticmethod
    def init_model(db):
        class UserModel(User, db.Model):
            __tablename__ = 'user'
            id = db.Column(db.Integer, primary_key=True)
            username = db.Column(db.String(80), unique=True, nullable=False)
            password = db.Column(db.String(120), nullable=False)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            downloads = db.relationship('Download', backref='user', lazy=True)
            movie_lists = db.relationship('MovieList', backref='creator', lazy=True)
            
        class Download(db.Model):
            __tablename__ = 'download'
            id = db.Column(db.Integer, primary_key=True)
            movie_id = db.Column(db.String(120), nullable=False)
            movie_title = db.Column(db.String(200), nullable=False)
            year = db.Column(db.String(4))
            rating = db.Column(db.String(10))
            magnet = db.Column(db.Text, nullable=False)
            imdb_code = db.Column(db.String(20))
            download_date = db.Column(db.DateTime, default=datetime.utcnow)
            status = db.Column(db.String(20), default='pendiente')
            user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
        
        class MovieList(db.Model):
            __tablename__ = 'movie_list'
            id = db.Column(db.Integer, primary_key=True)
            title = db.Column(db.String(200), nullable=False)
            description = db.Column(db.Text)
            share_code = db.Column(db.String(32), unique=True, nullable=False, default=lambda: uuid.uuid4().hex)
            is_public = db.Column(db.Boolean, default=False)
            created_at = db.Column(db.DateTime, default=datetime.utcnow)
            updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
            creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
            movies = db.relationship('MovieListItem', backref='movie_list', lazy=True, cascade='all, delete-orphan')
        
        class MovieListItem(db.Model):
            __tablename__ = 'movie_list_item'
            id = db.Column(db.Integer, primary_key=True)
            movie_title = db.Column(db.String(200), nullable=False)
            year = db.Column(db.String(4))
            rating = db.Column(db.String(10))
            imdb_code = db.Column(db.String(20))
            poster_url = db.Column(db.String(500))
            added_at = db.Column(db.DateTime, default=datetime.utcnow)
            notes = db.Column(db.Text)
            watched = db.Column(db.Boolean, default=False)
            list_id = db.Column(db.Integer, db.ForeignKey('movie_list.id'), nullable=False)
        
        return UserModel, Download, MovieList, MovieListItem
