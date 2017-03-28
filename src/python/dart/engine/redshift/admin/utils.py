import os

import boto3
import requests


def lookup_credentials(action):
    """ :type action: dart.model.action.Action """
    if not action.data.batch_job_id:
        # we are running locally and they should be set on the ENV
        return os.environ['AWS_ACCESS_KEY_ID'], os.environ['AWS_SECRET_ACCESS_KEY'], None

    # we are inside AWS using an instance profile... so now we get instance profile data
    results = requests.get('http://169.254.169.254/latest/meta-data/iam/info').json()
    instance_profile_arn = results['InstanceProfileArn']
    instance_profile_name = instance_profile_arn.split('instance-profile/')[1]

    # then we retrieve temporary credentials from the dart single-role instance profile
    results = boto3.client('iam').get_instance_profile(InstanceProfileName=instance_profile_name)
    role_name = results['InstanceProfile']['Roles'][0]['RoleName']
    results = requests.get('http://169.254.169.254/latest/meta-data/iam/security-credentials/%s' % role_name).json()
    return results['AccessKeyId'], results['SecretAccessKey'], results['Token']


def sanitized_query(sql):
    return sql.replace('%', '%%')
