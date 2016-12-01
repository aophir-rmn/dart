#!/usr/bin/env python

import subprocess
import sys

__author__ = 'dmcpherson'


def call(cmd):
    try:
        print cmd
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=True)
        print result
        return result
    except subprocess.CalledProcessError as e:
        print e.output
        raise e

# example: k1=v1 k2=v2 rmn:dw:emr:data_tools_s3_root=s3://bucket/path/file
tag_strings = sys.argv[1:]

instance_id = call("curl -s 'http://169.254.169.254/latest/meta-data/instance-id'")

tags = ["""'Key="%s",Value="%s"'""" % tuple(key_value.split('=')) for key_value in tag_strings]

call("""aws ec2 create-tags --resources %s --tags %s""" % (instance_id, ' '.join(tags)))
