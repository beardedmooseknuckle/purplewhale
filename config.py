# Do not edit this file directly, override using config files in instance/ folder

DEBUG = False # Disable Flask debugging
SQL_DEBUGGING = False # Disable Pony debugging
REMEMBER_COOKIE_SECURE = True
REMEMBER_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = True
SQLALCHEMY_TRACK_MODIFICATIONS = False # Adds significant overhead, and will be disabled in the future

# Database settings (shouldn't be overriden)
FRONTEND_BINDKEY = 'frontend'
FE_TBL_USERS = 'fe_users'
FE_TBL_CHANNELS = 'fe_channels'
FE_TBL_UID2CID = 'fe_uid2cid'
CHATBOT_BINDKEY = 'chatbot'
CB_TBL_MESSAGES = 'cb_messages'
CB_TBL_NOTICES = 'cb_notices'
CB_TBL_USERS = 'cb_users'
CB_TBL_CHANNELS = 'cb_channels'