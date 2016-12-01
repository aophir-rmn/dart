#!/usr/bin/env python27

import json
import sys
import subprocess
from datetime import datetime


def call(cmd):
    try:
        print cmd
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        print result
        return result
    except subprocess.CalledProcessError as e:
        print e.output
        raise e

hdfs_src = sys.argv[1].rstrip('/')
s3_dst = sys.argv[2].rstrip('/')
s3_stg_tmp = sys.argv[3].rstrip('/')


def get_s3_stg():
    tags_json = call('aws ec2 describe-tags --max-items 1 --filters "Name=key,Values=aws:elasticmapreduce:job-flow-id"')
    cluster_id = json.loads(tags_json)['Tags'][0]['Value']
    return '%s/%s/%s' % (s3_stg_tmp, cluster_id, datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S-%f'))


s3_stg = get_s3_stg()

assert s3_stg.startswith('s3://')

# first copy to an s3 staging area...
call("s3-dist-cp --src %s/ --dest %s/" % (hdfs_src, s3_stg))

# ...then to the target location
call('aws s3 mv --recursive %s/ %s/' % (s3_stg, s3_dst))
