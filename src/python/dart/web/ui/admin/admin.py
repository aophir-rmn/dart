import os
from flask import Blueprint
from sqlalchemy import text

from dart.context.database import db
from dart.model.mutex import Mutexes, MutexState
from dart.util.rand import random_id
from dart.config.config import configuration

admin_bp = Blueprint('admin', __name__)

CONFIG_PATH = os.environ['DART_CONFIG']
CONFIG = configuration(CONFIG_PATH)
AUTH_CONFIG = CONFIG['auth']

def exec_sql(statement):
    db.session.execute(statement)
    db.session.commit()


def populate_dart_client_apikeys(credential, secret, dart_client_user):
    del_sql = """ DELETE FROM public.api_key  WHERE (user_id = :user_id) """
    exec_sql(text(del_sql).bindparams(user_id=dart_client_user))


    add_sql = """INSERT INTO public.api_key(id, version_id, created, updated, user_id, api_key, api_secret)
      SELECT :id, 0, NOW(), NOW(),:user_id, :dart_client_key, :dart_client_secret
    """
    statement = text(add_sql).bindparams(id=random_id(),
                                     user_id=dart_client_user,
                                     dart_client_key=credential,
                                     dart_client_secret=secret)
    exec_sql(statement)


def populate_dart_client_user(dart_client_user):
    sql = """DELETE FROM public.user  WHERE (email = :email) """
    exec_sql(text(sql).bindparams(email=dart_client_user))

    sql = """ INSERT INTO public.user (id, version_id, created, updated, email, first_name, last_name, is_authenticated, session_expiration)
              SELECT :id, 0, NOW(), NOW(), :email, :email, :email, FALSE , NOW()"""
    exec_sql(text(sql).bindparams(id=random_id(), email=dart_client_user))

@admin_bp.route('/create_all', methods=['POST'])
def create_all():
    db.create_all()

    for mutex in Mutexes.all():
        sql = """
            INSERT INTO mutex (id, version_id, created, updated, name, state)
            SELECT :id, 0, NOW(), NOW(), :name, :state
            WHERE NOT EXISTS (SELECT NULL FROM mutex WHERE name = :name)
            """
        statement = text(sql).bindparams(id=random_id(), name=mutex, state=MutexState.READY)
        db.session.execute(statement)
        db.session.commit()


    # config values for dart_client_key/secret are extracted.
    if AUTH_CONFIG.get('use_auth'):
        if AUTH_CONFIG.get('dart_client_key') and AUTH_CONFIG.get('dart_client_secret'):
            _credential = AUTH_CONFIG.get('dart_client_key')
            _secret = AUTH_CONFIG.get('dart_client_secret')
        else:
            raise Exception("dart_client_key and dart_client_secret must both exist.")
    else:
        # The credential/secret default values are set in order to prevent exception while calculating to hmac.
        _credential = "cred"
        _secret = "secret"

    # We set a user for dart_client with a apikey/secret (read from config) so that dart_Client can work.
    # api auth expects a user to exist in the user table and have an entry in the api_key table (with key/secret values set).
    DART_CLIENT_USER = 'dart@client.rmn'
    populate_dart_client_user(DART_CLIENT_USER)
    populate_dart_client_apikeys(_credential, _secret, DART_CLIENT_USER)

    return 'OK'
