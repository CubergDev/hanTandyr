from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class FranchiseApplication(db.Model):
    __tablename__ = 'franchise_application'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    privacy_accepted = db.Column(db.Boolean, default=False)
    telegram_handle = db.Column(db.String(100), nullable=True)
    lang = db.Column(db.String(5), nullable=False, default='ru')

class TelegramUser(db.Model):
    __tablename__ = 'telegram_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    chat_id = db.Column(db.BigInteger, unique=True)
    is_admin = db.Column(db.Boolean, default=False)
