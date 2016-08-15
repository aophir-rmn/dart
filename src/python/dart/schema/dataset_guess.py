def dataset_guess_schema():
    return {
        'type': 'object',
        'properties': {
            's3_path': {'type': ['string', 'null'], 'pattern': '^s3://.+$'},
            'max_lines': {'type': ['integer', 'null'], 'maximum': 5000},
        },
        'additionalProperties': False,
        'required': ['s3_path', 'max_lines']
    }
