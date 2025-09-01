from flask_login import UserMixin
from datetime import datetime

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
        
        return UserModel, Download
