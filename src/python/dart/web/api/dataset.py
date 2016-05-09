import json

from flask import Blueprint, request, current_app
from flask.ext.jsontools import jsonapi

from dart.model.dataset import Dataset
from dart.schema.dataset import dataset_schema
from dart.service.dataset import DatasetService
from dart.service.filter import FilterService
from dart.web.api.entity_lookup import fetch_model
from dart.util.hunch import infer_dataset_data

api_dataset_bp = Blueprint('api_dataset', __name__)


@api_dataset_bp.route('/dataset', methods=['POST'])
@jsonapi
def post_dataset():
    return {'results': dataset_service().save_dataset(Dataset.from_dict(request.get_json())).to_dict()}


@api_dataset_bp.route('/dataset/<dataset>', methods=['GET'])
@fetch_model
@jsonapi
def get_dataset(dataset):
    return {'results': dataset.to_dict()}


@api_dataset_bp.route('/dataset/guess', methods=['GET'])
@jsonapi
def get_dataset_guess():
    s3_path = request.args.get('s3path')
    max_lines = request.args.get('maxlines')
    best_guess_schema = dataset_schema()
    best_guess_dataset = infer_dataset_data(s3_path, max_lines)
    best_guess_schema['properties']['data']['properties']['columns'] = best_guess_dataset.to_dict()
    return {'results': best_guess_schema}


@api_dataset_bp.route('/dataset', methods=['GET'])
@jsonapi
def find_datasets():
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    filters = [filter_service().from_string(f) for f in json.loads(request.args.get('filters', '[]'))]
    datasets = dataset_service().query_datasets(filters, limit, offset)
    return {
        'results': [d.to_dict() for d in datasets],
        'limit': limit,
        'offset': offset,
        'total': dataset_service().query_datasets_count(filters)
    }


@api_dataset_bp.route('/dataset/<dataset>', methods=['PUT'])
@fetch_model
@jsonapi
def put_dataset(dataset):
    return {'results': dataset_service().update_dataset(dataset.id, Dataset.from_dict(request.get_json())).to_dict()}


@api_dataset_bp.route('/dataset/<dataset>', methods=['DELETE'])
@fetch_model
@jsonapi
def delete_dataset(dataset):
    dataset_service().delete_dataset(dataset.id)
    return {'results': 'OK'}


def filter_service():
    """ :rtype: dart.service.filter.FilterService """
    return current_app.dart_context.get(FilterService)


def dataset_service():
    """ :rtype: dart.service.dataset.DatasetService """
    return current_app.dart_context.get(DatasetService)
