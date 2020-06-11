from connexion.exceptions import OAuthProblem
from ..models import User

def apikey_auth(apikey, required_scopes=None):
  """ Simple function to validate an API key and retrieve the user's information in the process """
  api_user = User.query.filter_by(api_token=apikey).first()
  
  if api_user is None:
      raise OAuthProblem('Invalid API key')

  return api_user

def get_users_list(api_user):
  pass

def get_users(api_user, user_name):
  pass

def get_user_logs(api_user, user_name):
  pass

def get_channels_list(api_user):
  pass

def get_channels(api_user, channel_name):
  pass

def get_channel_logs(api_user, channel_name):
  pass
  
def get_context(api_user, message_id):
  pass