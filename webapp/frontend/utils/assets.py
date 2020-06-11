from flask import current_app
from flask_assets import Bundle, Environment

bundles = {
    'frontend_js': Bundle(
        'js/libs/jquery-3.5.0.min.js',
        'js/libs/popper.min.js',
        'js/libs/bootstrap.min.js',
        output='assets/frontend.min.js',
        filters='jsmin'),

    'frontend_css': Bundle(
        'css/libs/bootstrap.min.css',
        'css/cover.css',
        'css/frontend.css',
        output='assets/frontend.min.css',
        filters='cssmin'),
}

assets = Environment(current_app)

assets.register(bundles)