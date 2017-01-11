import os

from flask.ext.sqlalchemy import SQLAlchemy, Model
from sqlalchemy import create_engine
import sqlalchemy.sql.expression
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from dart.config.config import configuration


class DartDbSession(object):
    def __init__(self, model, func, session):
        self.Model = model
        self.func = func
        self.session = session


def init_dart_db(database_uri_alias='SQLALCHEMY_DATABASE_URI'):
    engine = create_engine(config['flask'][database_uri_alias], convert_unicode=True)
    db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    base = declarative_base(cls=Model, name='Model')
    base.query = db_session.query_property()
    return DartDbSession(base, sqlalchemy.sql.expression.func, db_session)


config = configuration(os.environ['DART_CONFIG'])
db = SQLAlchemy() if os.environ.get('DART_ROLE') == 'web' else init_dart_db('SQLALCHEMY_DATABASE_URI')
db_replica = SQLAlchemy() if os.environ.get('DART_ROLE') == 'web' else init_dart_db('SQLALCHEMY_DATABASE_REPLICA_URI')
