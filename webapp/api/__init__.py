import connexion
from ..models import db

def create_app():
  """ Initialize the API application """
  app = connexion.FlaskApp(__name__, server_args={'instance_relative_config': True})
  app.app.config.from_object('config')
  app.app.config.from_pyfile('api.py')
  app.add_api('openapi.yaml')
    
  with app.app.app_context():
    db.init_app(app.app)
    
    from . import endpoints
        
    return app