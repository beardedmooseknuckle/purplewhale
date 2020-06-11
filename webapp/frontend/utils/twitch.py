import requests
from functools import wraps
from flask import current_app, flash, redirect, url_for
from flask_login import current_user, confirm_login
from datetime import datetime, timezone, timedelta
from .. import db

def get_oauth_keys():
    """ Download, if required, and cache Twitch OAuth2 keys to validate ID Token signatures
    Ref: https://dev.twitch.tv/docs/authentication/getting-tokens-oidc """
    keys = requests.get("https://id.twitch.tv/oauth2/keys")
    return keys.json()

def refresh_tokens():
    """
    Ref: https://dev.twitch.tv/docs/authentication/#refreshing-access-tokens """
    url = 'https://id.twitch.tv/oauth2/token'
    headers = { 'Authorization': f'OAuth {current_user.access_token}' }
    payload = { 'grant_type': 'refresh_token',
                'refresh_token': current_user.refresh_token,
                'client_id': current_app.config.get('TWITCH_CLIENT_ID'),
                'client_secret': current_app.config.get('TWITCH_CLIENT_SECRET')
                }
    r = requests.post(url, headers=headers, data=payload)
    j = r.json()
        
    # @todo better error handling?
    if j.get('error'):
        return False
    
    # Update our User object with new tokens
    current_user.access_token = j.get('access_token')
    current_user.refresh_token = j.get('refresh_token')
    current_user.expiry_date = datetime.now(timezone.utc)+timedelta(seconds=j.get('expires_in'))
    db.session.commit()
    
    return True

def validate_access_token():
    """ Twitch requires periodic (every hour) access token validation, and before API calls
    Ref: https://dev.twitch.tv/docs/authentication/#validating-requests """
    url = 'https://id.twitch.tv/oauth2/validate'
    headers = { 'Authorization': f'OAuth {current_user.access_token}' }
    r = requests.get(url, headers=headers)
    j = r.json()
    if (j.get('client_id') == current_app.config.get('TWITCH_CLIENT_ID')) and (int(j.get('user_id')) == current_user.user_id):
        # Update expiry date of the token
        current_user.expiry_date = datetime.now(timezone.utc)+timedelta(seconds=j.get('expires_in'))
        db.session.commit()
        return True
    else:
        return False

def check_access_token_expiry(fn):
    # Wraps required for url_for to work on a decorated function, other we return the wrong function name
    @wraps(fn)
    def wrapper_check_access_token_expiry():
        # If tokens are expirying in less than a minute, let's refresh ahead of time, even if Twitch doesn't like it
        # Find a better solution later, based on 401 invalid token errors to API requests, but we don't use them
        expiry_date = current_user.expiry_date.astimezone(timezone.utc)-timedelta(seconds=60)
        if datetime.now(timezone.utc) >= expiry_date:
           if not refresh_tokens():
                flash('Failed to refresh your Twitch tokens, please login back in.')
                return redirect(url_for('logout')) 
        if validate_access_token():
            # flash('Session refreshed')
            # Mark this user session as fresh!
            confirm_login()
            
            # Flask quirk, return is required when normally you'd omit it in a decorator
            # If omitted, the "view" function doesn't return and an exception is raised by Flask
            return fn()
        else:
            flash('Session expired, please log back in.')
            return redirect(url_for('login'))
    return wrapper_check_access_token_expiry