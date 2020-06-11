from twitchio.ext import commands
from pony.orm import db_session, set_sql_debug
from datetime import datetime, timezone
from chatbot.models import db, TwitchMessage, TwitchNotice, TwitchUser, TwitchChannel
from signal import signal, SIGINT
import os, logging

class TwitchBot(commands.Bot):
  def __init__(self, oauth_token, client_id, nick, prefix, channels):
    # Call parent class init
    super().__init__(irc_token=oauth_token,
                     client_id=client_id,
                     nick=nick,
                     prefix=prefix,
                     initial_channels=channels)
    
    # Exit gracefully on Ctrl-C by closing the queue/worker thread
    signal(SIGINT, self.sigint_handler)

    # Setup logging
    self.setup_logger()
    
    # User-friendly message on how to stop the bot
    self.logger.info("Chickaloon is running. Press CTRL-C to exit.")
  
  def sigint_handler(self, signal_received, frame):
    self.logger.info('SIGINT or CTRL-C detected. Exiting gracefully...')
    exit(0)

  def setup_logger(self):
    """Simple helper method to start our logging"""
    logs_path = os.path.join(os.getcwd(), "logs/")
    # Make sure our logs folder exists (exist_ok prevents an exception if folder exists)
    # @todo change the umask to restrict viewership?
    os.makedirs(logs_path, exist_ok=True)
    # Chickaloon Logging
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    self.logger = logging.getLogger("Chickaloon")
    self.logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    self.logger.addHandler(ch)
    fh = logging.FileHandler(f"{logs_path}chickaloon.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    self.logger.addHandler(fh)
    # Websockets Logging
    logger = logging.getLogger("websockets")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    logger.addHandler(ch)
    fh = logging.FileHandler(f"{logs_path}websockets.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)
  
  def bind_db(self, db_config, sql_debugging=False):
    # Attach our entities to the database
    db.bind(**db_config)
    
    # Enable/disable SQL debugging
    set_sql_debug(sql_debugging)

    # Generate the database mapping (check tables exist and as expected, but don't created them)
    db.generate_mapping(check_tables=True, create_tables=False)
    
    return True
  
  async def event_ready(self):
    """Called once when the bot goes online."""
    self.logger.info(f"{self.nick} is online!") 

  @db_session
  async def event_message(self, msg):
    """Runs every time a message is sent in chat."""
    if not (c := TwitchChannel.get(channel_name=msg.channel.name)):
      c = TwitchChannel(channel_id=msg.tags['room-id'], channel_name=msg.channel.name)
    elif c.channel_id == 0 and msg.tags['room-id']:
      c.channel_id = msg.tags['room-id'] # Update the channel row with its ID
    if not (u := TwitchUser.get(user_name=msg.author.name)):
      u = TwitchUser(user_id=msg.author.id, user_name=msg.author.name)
    elif u.user_id == 0 and msg.author.id:
      u.user_id = msg.author.id # Update the user row with its ID
    m = TwitchMessage(cid=c, uid=u, mid=msg.tags['id'], timestamp=msg.timestamp, content=msg.content)
    # Commits happen upon return, including updates to channel/user

  @db_session
  async def event_raw_usernotice(self, channel, tags):
    """Runs every time a subscription different from classic sub/resub happens."""
    if tags['msg-id'] in ('sub', 'resub', 'subgift', 'anonsubgift', 'submysterygift', 'giftpaidupgrade', 'rewardgift', 'anongiftpaidupgrade', 'raid', 'unraid', 'ritual', 'bitsbadgetier'):
      if not (c := TwitchChannel.get(channel_name=channel.name)):
        c = TwitchChannel(channel_id=tags['room-id'], channel_name=channel.name)
      elif c.channel_id == 0 and tags['room-id']:
        c.channel_id = tags['room-id'] # Update the channel row with its ID
      if not (u := TwitchUser.get(user_name=tags['login'])):
        u = TwitchUser(user_id=tags['user-id'], user_name=tags['login'])
      elif u.user_id == 0 and tags['user-id']:
        u.user_id = tags['user-id'] # Update the user row with its ID
      
      # Twitch sends this message with escaped spaces, so weird... #twitchthings
      system_msg = tags['system-msg'].replace('\\s', ' ')
      # TwitchIO does not provide a timestamp?! We'll make our own.
      utc_stamp = datetime.now(timezone.utc)
      notice_stamp = utc_stamp.strftime('%Y-%m-%d %H:%M:%S')

      m = TwitchNotice(cid=c, uid=u, mid=tags['id'], msg_id=tags['msg-id'], timestamp=notice_stamp, content=system_msg)
      # Commits happen upon return, including updates to channel/user

  async def event_raw_data(self, data):
    """Feeling cute, may use this in the future"""
    pass