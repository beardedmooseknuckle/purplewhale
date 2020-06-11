from flask import current_app, flash, g, redirect, render_template, request, session, url_for
from flask_login import confirm_login, current_user, login_required, login_user, logout_user
from authlib.jose import jwt
from authlib.common.security import generate_token
from datetime import datetime, timezone, timedelta

from . import db, login_manager, oauth
from .utils import assets, twitch
from ..models import User, Channel, TwitchMessage, TwitchUser

@login_manager.user_loader
def load_user(uid):
  return User.query.get(uid)

@login_manager.unauthorized_handler
def unauthorized():
  flash('Session timed out :( Investigating a bug where the session is destroyed when visiting the site after closing your browser.')
  return redirect(url_for('frontpage'))

@current_app.before_request
def before_request():
  if current_user.is_authenticated:
    g.user = current_user
  else:
    g.user = None

@current_app.route('/')
def frontpage():
  if current_user.is_authenticated:
    # Weird bug happening where only when accessing '/' after closing browser, our remember_me cookie is wiped
    # Confirming the login refreshes the cookie, prevents that bug or re-sets the cookie after it's deleted
    confirm_login()
    return redirect(url_for('dashboard'))
  else:
    return render_template('frontpage.html')

@current_app.route('/login')
def login():
  if current_user.is_authenticated:
    return redirect(url_for('dashboard'))
  else:
    # Nonce is used to associate the client’s authorization session with an ID token, preventing replay attacks.
    nonce = generate_token(20)
    session['OIDC_nonce'] = nonce
    params = {'nonce': nonce}
    redirect_uri = url_for('authorize', _external=True)
    return oauth.twitch.authorize_redirect(redirect_uri, **params)

@current_app.route('/authorize', methods=('POST','GET'))
def authorize():
  """ 
  @todo move this into login()? change url redirect on twitch for /login
  @todo better error handling, redirect to an error page with better troubleshooting/contact admin 
  @todo Cache the keys for X amount of time
  @todo Better nonce check? could someone pass their own nonce to defeat the condition check? !=? ==?
  """
  # Send user back to login if no nonce is set (shouldn't access /authorize directly)
  #if not session.get('OIDC_nonce'):
  #  return redirect(url_force('login'))
    
  # Make sure we received an auth code before requesting an access token
  if not request.values.get('code'):
    return "Invalid response during OpenID exchange with Twitch. (missing auth code)"
  else:
    token = oauth.twitch.authorize_access_token()
    if (token.get('nonce') != session.get('OIDC_nonce')):
      return "Unexpected response during OpenID exchange with Twitch. (mismatched nonce)"
    try:
      # Validate the ID Token by decoding it, exception raised if it fails
      jwt.decode(token.get('id_token'), twitch.get_oauth_keys())
    except jwt.BadSignatureError:
      return "Unexpected response during OpenID exchange with Twitch. (invalid id token)"
    claims = oauth.twitch.parse_id_token(token)
    # Confirm we're the audience for this ID Token
    if (claims.get('aud') != current_app.config.get('TWITCH_CLIENT_ID')):
      return "Unexpected response during OpenID exchange with Twitch. (mismatched audience)"
    # Oof! Pass the information on to the handler
    return handle_authorize(token, claims)

def handle_authorize(token, claims):  
  # Get user, or create him if needed
  u = User.query.filter_by(user_id=claims.get('sub')).first()
  if u is None:
    # Replace the u variable with a new User object
    u = User(
      user_id = claims.get('sub'),
      preferred_name = claims.get('preferred_username'),
      )
    # Ensures at least one admin can login to manage users
    if claims.get('preferred_username') in current_app.config.get('SUPER_ADMINS'):
      u.admin = True
      u.authorized = True
    db.session.add(u)
    db.session.commit()
  
  # Update OAuth information
  u.access_token = token.get('access_token')
  u.refresh_token = token.get('refresh_token')
  u.expiry_date = datetime.now(timezone.utc)+timedelta(seconds=token.get('expires_in'))
  db.session.commit()
  
  # Save user information in a session
  login_user(u, remember=True)
  
  # Follow-on message confirming user logged in
  flash('Logged in successfully.')
  
  # Send user to dashboard
  return redirect(url_for('dashboard'))

@current_app.route('/dashboard')
@login_required
@twitch.check_access_token_expiry
def dashboard():
  if not current_user.is_authorized:
    return render_template('unauthorized.html')
  else:
    if (searched_user := request.values.get('u')):
      g.searched_user = searched_user
      g.lines = db.session.query(TwitchMessage, TwitchUser).join(TwitchUser).filter(TwitchUser.user_name==searched_user).order_by(TwitchMessage.timestamp.desc()).limit(50).all()
    else:
      g.searched_user = None
      g.lines = None
    return render_template('dashboard.html')

@current_app.route("/admin")
@login_required
@twitch.check_access_token_expiry
def admin():
  if not current_user.is_admin:
    return render_template('unauthorized.html')
  else:
    # @todo improve validation/logic (invalid user IDs, etc.)
    if (authorized_user := request.values.get('authorize_access')):
      u = User.query.get(authorized_user)
      u.authorized = True
      db.session.commit()
      flash(f'Authorized access to `{u.preferred_name}`')
    if (revoked_user := request.values.get('revoke_access')):
      u = User.query.get(revoked_user)
      if u.preferred_name in current_app.config.get('SUPER_ADMINS'):
        flash('Cannot revoke access to super admins')
      else:
        u.authorized = False
        db.session.commit()
        flash(f'Revoked access to `{u.preferred_name}`')
    g.users = User.query.all()
    return render_template('admin.html')
  
@current_app.route("/logout")
@login_required
def logout():
  # Clear OAuth information
  current_user.access_token = None
  current_user.refresh_token = None
  current_user.expiry_date = None
  db.session.commit()

  # Clear session information
  logout_user()
  
  # Send user to frontpage
  return redirect(url_for('frontpage'))