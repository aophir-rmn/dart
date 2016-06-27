from sqlalchemy.exc import IntegrityError as SqlAlchemyIntegrityError
from psycopg2._psycopg import IntegrityError as PostgresIntegrityError
from dart.context.locator import injectable
from dart.model.exception import DartValidationException
from dart.model.orm import AccountingDao
from dart.context.database import db
from dart.service.patcher import retry_stale_data
from dart.util.rand import random_id


@injectable
class AccountingService(object):
    def __init__(self):
        pass

    @staticmethod
    def save_accounting_event(accounting_event, commit=True, flush=False):
        """ :type accounting_event: dart.model.accounting.Accounting """

        accounting_dao = AccountingDao()
        accounting_dao.id = random_id()
        accounting_dao.user_id = accounting_event.user_id
        accounting_dao.state = accounting_event.state
        accounting_dao.entity = accounting_event.entity
        accounting_dao.params = accounting_event.params
        accounting_dao.return_code = accounting_event.return_code
        accounting_dao.api_version = accounting_event.api_version
        accounting_dao.extra = accounting_event.extra

        db.session.add(accounting_dao)
        try:
            if flush:
                db.session.flush()
            if commit:
                db.session.commit()
#            accounting_event = accounting_dao.to_model()
            return accounting_event
        except SqlAlchemyIntegrityError as e:
            if hasattr(e, 'orig') and isinstance(e.orig, PostgresIntegrityError) and e.orig.pgcode == '23505':
                raise DartValidationException('name already exists: %s' % dataset.data.name)
            raise e

    @staticmethod
    @retry_stale_data
    def update_dataset_data(accounting_event_id, dataset_data):
        accounting_dao = AccountingDao.query.get(accounting_event_id)
        accounting_dao.user_id = dataset_data.user_id
        accounting_dao.state = dataset_data.state
        accounting_dao.entity = dataset_data.entity
        accounting_dao.params = dataset_data.params
        accounting_dao.return_code = dataset_data.return_code
        accounting_dao.api_version = dataset_data.api_version
        accounting_dao.extra = dataset_data.extra


        db.session.commit()
        return dataset_dao.to_model()

    @staticmethod
    @retry_stale_data
    def delete_dataset(accounting_event_id):
        accounting_dao = DatasetDao.query.get(accounting_event_id)
        db.session.delete(accounting_dao)
        db.session.commit()
