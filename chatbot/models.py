from config import *
# @todo support overriding database bind/table names with a database.py in instance/ folder
from pony.orm import *
from datetime import datetime

db = Database()

class TwitchMessage(db.Entity):
  _table_ = CB_TBL_MESSAGES
  id = PrimaryKey(int, size=32, unsigned=True, auto=True)
  cid = Required('TwitchChannel')
  uid = Required('TwitchUser')
  mid = Optional(str)
  timestamp = Required(datetime)
  content = Required(str, max_len=500)

class TwitchNotice(db.Entity):
  _table_ = CB_TBL_NOTICES
  id = PrimaryKey(int, size=32, unsigned=True, auto=True)
  cid = Required('TwitchChannel')
  uid = Required('TwitchUser')
  mid = Optional(str)
  msg_id = Optional(str)
  timestamp = Required(datetime)
  content = Required(str, max_len=500)
  
class TwitchUser(db.Entity):
  _table_ = CB_TBL_USERS
  id = PrimaryKey(int, size=32, unsigned=True, auto=True)
  user_id = Optional(int, size=32, unsigned=True, index=True)
  user_name = Required(str, index=True)
  messages = Set('TwitchMessage')
  notices = Set('TwitchNotice')

class TwitchChannel(db.Entity):
  _table_ = CB_TBL_CHANNELS
  id = PrimaryKey(int, size=32, unsigned=True, auto=True)
  channel_id = Optional(int, size=32, unsigned=True, index=True)
  channel_name = Required(str, index=True)
  messages = Set('TwitchMessage')
  notices = Set('TwitchNotice')