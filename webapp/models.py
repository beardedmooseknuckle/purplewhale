from config import *
from flask_sqlalchemy import SQLAlchemy
from datetime import timezone

db = SQLAlchemy()

# Many-to-many table used to associate frontend users access to channels
channels = db.Table(
  FE_TBL_UID2CID,
  db.Column('uid', db.Integer, db.ForeignKey(f'{FE_TBL_USERS}.id'), primary_key=True),
  db.Column('cid', db.Integer, db.ForeignKey(f'{FE_TBL_CHANNELS}.id'), primary_key=True),
  info = { 'bind_key': FRONTEND_BINDKEY }
  )

class User(db.Model):
  __bind_key__ = FRONTEND_BINDKEY
  __tablename__ = FE_TBL_USERS

  id = db.Column(db.Integer, primary_key=True)
  # Twitch-specific (for the API/login integration)
  user_id = db.Column(db.Integer, index=True, nullable=False)
  preferred_name = db.Column(db.String(255), index=True, nullable=False)
  access_token = db.Column(db.String(255))
  refresh_token = db.Column(db.String(255))
  expiry_date = db.Column(db.DateTime(timezone.utc))
  # PurpleWhale-specific
  api_key = db.Column(db.String(255), index=True)
  authorized = db.Column(db.Boolean, default=False, nullable=False)
  admin = db.Column(db.Boolean, default=False, nullable=False)
  prefs = db.Column(db.JSON) # not yet implemented on the frontend, meant to store user preferences (default context size, timezone, etc.)
  channels = db.relationship('Channel', secondary=channels, lazy='subquery', backref=db.backref(FE_TBL_USERS, lazy=True))
  
  @property
  def is_active(self):
      return True
  
  @property
  def is_admin(self):
    """ Property used by API to bypass rate limits for admins """
    if self.admin:
      return True
    else:
      return False

  @property
  def is_anonymous(self):
      return False

  @property
  def is_authenticated(self):
      return True
      
  @property
  def is_authorized(self):
    """ Property used by API to ensure user is authorized to access logs """
    if self.authorized:
      return True
    else:
      return False

  def get_id(self):
      try:
          return str(self.id)
      except AttributeError:
          raise NotImplementedError('No `id` attribute - override `get_id`')

class Channel(db.Model):
  __bind_key__ = FRONTEND_BINDKEY
  __tablename__ = FE_TBL_CHANNELS
  
  id = db.Column(db.Integer, primary_key=True)
  channel_id = db.Column(db.Integer, index=True, nullable=False)
  channel_name = db.Column(db.String(255), index=True, nullable=False)

class TwitchMessage(db.Model):
  __bind_key__ = CHATBOT_BINDKEY
  __tablename__ = CB_TBL_MESSAGES
  id = db.Column(db.Integer, primary_key=True)
  cid = db.Column(db.Integer, db.ForeignKey(f'{CB_TBL_CHANNELS}.id'), index=True, nullable=False)
  uid = db.Column(db.Integer, db.ForeignKey(f'{CB_TBL_USERS}.id'), index=True, nullable=False)
  mid = db.Column(db.String(255), nullable=True)
  timestamp = db.Column(db.DateTime(timezone.utc), nullable=False)
  content = db.Column(db.Text(), nullable=False)

class TwitchUser(db.Model):
  __bind_key__ = CHATBOT_BINDKEY
  __tablename__ = CB_TBL_USERS
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, index=True, nullable=False)
  user_name = db.Column(db.String(255), index=True, nullable=False)
  #messages = db.relationship('TwitchMessage', backref='user', lazy=True)
    
class TwitchChannel(db.Model):
  __bind_key__ = CHATBOT_BINDKEY
  __tablename__ = CB_TBL_CHANNELS
  id = db.Column(db.Integer, primary_key=True)
  channel_id = db.Column(db.Integer, index=True, nullable=False)
  channel_name = db.Column(db.String(255), index=True, nullable=False)