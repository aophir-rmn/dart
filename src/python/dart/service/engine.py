import boto3
import jsonpatch
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError as SqlAlchemyIntegrityError
from psycopg2._psycopg import IntegrityError as PostgresIntegrityError
from sqlalchemy.orm.exc import NoResultFound

from dart.context.locator import injectable
from dart.model.exception import DartValidationException, DartRequestException
from dart.model.orm import EngineDao, SubGraphDefinitionDao
from dart.context.database import db
from dart.schema.action import action_schema
from dart.schema.base import default_and_validate
from dart.schema.datastore import datastore_schema
from dart.schema.engine import engine_schema, subgraph_definition_schema
from dart.service.patcher import retry_stale_data
from dart.util.rand import random_id


@injectable
class EngineService(object):
    def __init__(self, filter_service, dart_config):
        self._filter_service = filter_service
        self._engine_taskrunner_ecs_cluster = dart_config['dart'].get('engine_taskrunner_ecs_cluster')
        self._engine_task_definition_max_total_memory_mb =\
            dart_config['dart'].get('engine_task_definition_max_total_memory_mb')

    def save_engine(self, engine):
        """ :type engine: dart.model.engine.Engine """
        engine = default_and_validate(engine, engine_schema())
        self._validate_ecs_task_definition(engine.data.ecs_task_definition)

        engine_dao = EngineDao()
        engine_dao.id = random_id()
        engine_dao.name = engine.data.name
        engine_dao.data = engine.data.to_dict()
        db.session.add(engine_dao)
        try:
            db.session.commit()
            engine = engine_dao.to_model()
            engine.data.ecs_task_definition_arn = self._register_ecs_task_definition(engine)
            return self.update_engine_data(engine.id, engine.data)

        except SqlAlchemyIntegrityError as e:
            if hasattr(e, 'orig') and isinstance(e.orig, PostgresIntegrityError) and e.orig.pgcode == '23505':
                raise DartValidationException('name already exists: %s' % engine.data.name)
            raise e

    def _validate_ecs_task_definition(self, ecs_task_definition):
        if not ecs_task_definition:
            return
        for cd in ecs_task_definition['containerDefinitions']:
            if 'memory' not in cd:
                DartValidationException('every containerDefinition must specify memory requirements')
        mx = self._engine_task_definition_max_total_memory_mb
        mem = sum([cd['memory'] for cd in ecs_task_definition['containerDefinitions']])
        if mem > mx:
            raise DartValidationException('ecs task definition requires %s mb of memory, but the max is %s' % mem, mx)

    def _register_ecs_task_definition(self, engine):
        """ :type engine: dart.model.engine.Engine """
        if not self._engine_taskrunner_ecs_cluster or not engine.data.ecs_task_definition:
            return None
        response = boto3.client('ecs').register_task_definition(
            family=engine.data.ecs_task_definition.get('family'),
            containerDefinitions=engine.data.ecs_task_definition.get('containerDefinitions'),
            volumes=engine.data.ecs_task_definition.get('volumes')
        )

        taskdef_arn = response['taskDefinition']['taskDefinitionArn']
        if taskdef_arn is None:
            raise DartRequestException('No change to task definition')

        return taskdef_arn

    def _deregister_task_definition(self, ecs_task_definition_arn):
        if self._engine_taskrunner_ecs_cluster and ecs_task_definition_arn:
            boto3.client('ecs').deregister_task_definition(taskDefinition=ecs_task_definition_arn)

    @staticmethod
    def save_subgraph_definition(subgraph_definition, engine, trigger_schemas):
        """ :type engine: dart.model.engine.Engine
            :type subgraph_definition: dart.model.graph.SubGraphDefinition """
        action_schemas = [action_schema(e.params_json_schema) for e in engine.data.supported_action_types]
        ds_schema = datastore_schema(engine.data.options_json_schema)
        schema = subgraph_definition_schema(trigger_schemas, action_schemas, ds_schema)
        subgraph_definition = default_and_validate(subgraph_definition, schema)
        subgraph_definition_dao = SubGraphDefinitionDao()
        subgraph_definition_dao.id = random_id()
        subgraph_definition_dao.data = subgraph_definition.data.to_dict()
        subgraph_definition_dao.data['engine_name'] = engine.data.name
        db.session.add(subgraph_definition_dao)
        db.session.commit()
        return subgraph_definition_dao.to_model()

    @staticmethod
    @retry_stale_data
    def delete_subgraph_definition(subgraph_definition_id):
        subgraph_definition_dao = SubGraphDefinitionDao.query.get(subgraph_definition_id)
        db.session.delete(subgraph_definition_dao)
        db.session.commit()

    @staticmethod
    def get_subgraph_definitions(engine_name):
        query = SubGraphDefinitionDao.query\
            .filter(SubGraphDefinitionDao.data['engine_name'].as_text == engine_name)\
            .order_by(desc(SubGraphDefinitionDao.created))
        return [e.to_model() for e in query.all()]

    @staticmethod
    def get_subgraph_definition(subgraph_definition_id, raise_when_missing=True):
        subgraph_definition_dao = SubGraphDefinitionDao.query.get(subgraph_definition_id)
        if not subgraph_definition_dao and raise_when_missing:
            raise Exception('subgraph_definition with id=%s not found' % subgraph_definition_id)
        return subgraph_definition_dao.to_model() if subgraph_definition_dao else None

    @staticmethod
    def get_engine(engine_id, raise_when_missing=True):
        engine_dao = EngineDao.query.get(engine_id)
        if not engine_dao and raise_when_missing:
            raise Exception('engine with id=%s not found' % engine_id)
        return engine_dao.to_model() if engine_dao else None

    @staticmethod
    def get_engine_by_name(engine_name, raise_when_missing=True):
        """ :rtype: dart.model.engine.Engine """
        try:
            engine_dao = EngineDao.query.filter(EngineDao.name == engine_name).one()
            return engine_dao.to_model()
        except NoResultFound:
            if raise_when_missing:
                raise Exception('engine with name=%s not found' % engine_name)
            return None

    def all_engine_names(self):
        return [e.data.name for e in self.query_engines([], 1000, 0)]

    def query_engines(self, filters, limit=20, offset=0):
        """ :type filters: list[dart.model.query.Filter] """
        query = self._query_engine_query(filters)
        query = query.limit(limit).offset(offset)
        return [e.to_model() for e in query.all()]

    def query_engines_count(self, filters):
        """ :type filters: list[dart.model.query.Filter] """
        query = self._query_engine_query(filters)
        return query.count()

    def _query_engine_query(self, filters):
        query = EngineDao.query.order_by(EngineDao.updated)
        for f in filters:
            query = self._filter_service.apply_filter(f, query, EngineDao, [engine_schema()])
        return query

    def update_engine(self, engine, updated_engine):
        updated_engine = default_and_validate(updated_engine, engine_schema())
        self._validate_ecs_task_definition(updated_engine.data.ecs_task_definition)

        p = jsonpatch.make_patch(engine.data.ecs_task_definition, updated_engine.data.ecs_task_definition)
        prior_arn_missing = not engine.data.ecs_task_definition_arn and updated_engine.data.ecs_task_definition
        if len(p.patch) > 0 or prior_arn_missing:
            self._deregister_task_definition(engine.data.ecs_task_definition_arn)
            updated_engine.data.ecs_task_definition_arn = self._register_ecs_task_definition(updated_engine)

        return self.update_engine_data(engine.id, updated_engine.data)

    @staticmethod
    @retry_stale_data
    def update_engine_data(engine_id, engine_data):
        engine_dao = EngineDao.query.get(engine_id)
        engine_dao.name = engine_data.name
        engine_dao.data = engine_data.to_dict()
        db.session.commit()
        return engine_dao.to_model()

    def delete_engine(self, engine):
        self._deregister_task_definition(engine.data.ecs_task_definition_arn)
        self._delete_engine(engine)

    @staticmethod
    @retry_stale_data
    def _delete_engine(engine):
        SubGraphDefinitionDao.query\
            .filter(SubGraphDefinitionDao.data['engine_name'].astext == engine.data.name)\
            .delete(synchronize_session='fetch')
        engine_dao = EngineDao.query.get(engine.id)
        db.session.delete(engine_dao)
        db.session.commit()
