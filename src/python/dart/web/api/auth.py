import json

from flask import Blueprint, request, current_app, make_response, redirect, flash, url_for
from flask.ext.login import login_required, LoginManager, UserMixin, login_user, logout_user
from urlparse import urlparse
from datetime import datetime

from dart.service.user import UserService

auth_bp = Blueprint('auth', __name__)

login_manager = LoginManager()

@auth_bp.route('/login', methods=['GET'])
@login_manager.unauthorized_handler
def get_login():
    auth = current_app.auth_class(request)
    return auth.handle_login_request()

@auth_bp.route('/login', methods=['POST'])
def post_login():
    auth = current_app.auth_class(request)
    user = auth.process_login_response()
    if user.is_authenticated:
        login_user(user)
        return redirect(request.args.get('next') or '/')
    flash('Login incorrect')
    return redirect(url_for('auth.get_login'))

@auth_bp.route('/logout', methods=['GET'])
def logout():
    auth = current_app.auth_class(request)
    auth.handle_logout_request()
    logout_user()
    flash('logged out')
    return redirect('/')

@login_manager.user_loader
def load_user(user_id):
    user_service = current_app.dart_context.get(UserService)
    user = user_service.get_user(user_id, False)
    user.is_authenticated = (user.is_authenticated and user.session_expiration > datetime.utcnow())
    return user
