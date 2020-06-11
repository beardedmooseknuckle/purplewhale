from config import *
from instance.chatbot import *
from chatbot.twitchbot import TwitchBot

def create_app():
  # Create our bot instance and start botting!
  app = TwitchBot(
          TWITCH_OAUTH_TOKEN,
          TWITCH_CLIENT_ID,
          TWITCH_BOT_NICK,
          TWITCH_BOT_PREFIX,
          TWITCH_CHANNELS)
  
  app.bind_db(DATABASE_CONFIG, SQL_DEBUGGING)
  
  return app

def init_db():
  from pony.orm import set_sql_debug
  from chatbot.models import db

  # Attach our entities to the database
  db.bind(**DATABASE_CONFIG)
  
  # Disable SQL debugging
  set_sql_debug(SQL_DEBUGGING)

  # Generate the database mapping (create tables as needed)
  db.generate_mapping(create_tables=True)
  
  return True