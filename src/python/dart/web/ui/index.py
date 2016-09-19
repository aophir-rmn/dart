from flask import Blueprint, render_template, session
from dart.web.api.entity_lookup import check_login

index_bp = Blueprint('index', __name__)


@index_bp.route('/')
def index():
    print "### index '/' %s " % session.get("user_id")
    # Forcing user to authenticate if he is not.
    # This is a work around since python-saml & Flask-login should have made this redirect.
    if not session.get("user_id"):
        print "### render 'info'"
        return render_template("info.html")

    return render_template('index.html')


@index_bp.route('/info')
def info():
    return render_template('info.html')
