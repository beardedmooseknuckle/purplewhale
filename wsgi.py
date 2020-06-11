from werkzeug.middleware.dispatcher import DispatcherMiddleware
from webapp.api import create_app as api_create_app
from webapp.frontend import create_app as frontend_create_app

api = api_create_app()
frontend = frontend_create_app()

app = DispatcherMiddleware(frontend, {
  '/api': api
})