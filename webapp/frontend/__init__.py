from flask import Flask
from flask_login import LoginManager
from authlib.integrations.flask_client import OAuth
from ..models import db

login_manager = LoginManager()
oauth = OAuth()

def create_app():
  """ Initialize the frontend application """
  app = Flask(__name__, instance_relative_config=True)
  app.config.from_object('config')
  app.config.from_pyfile('frontend.py')

  db.init_app(app)

  oauth.init_app(app)
  oauth.register(
      name='twitch',
      server_metadata_url='https://id.twitch.tv/oauth2/.well-known/openid-configuration',
      # Required, otherwise our client id/secret aren't sent and Twitch kicks back error 400 (client id missing)
      token_endpoint_auth_method='client_secret_post',
      revocation_endpoint_auth_method='client_secret_post',
      client_kwargs={
          'scope': 'openid'
      },
  )

  login_manager.init_app(app)
  login_manager.session_protection = "strong" # If cookie is lost, force login
  
  with app.app_context():
    from . import views
    return app

def init_db():
  """ Create required database tables for PurpleWhale Flask applications """
  app = create_app()
  
  with app.app_context():
    # create_all is far from ideal, it doesn't return, and if tables exist, structure isn't validated and no exception is raised
    db.create_all(bind='frontend') # For now, stick to the frontend
    return True