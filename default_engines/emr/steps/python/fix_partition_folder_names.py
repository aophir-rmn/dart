#!/usr/bin/env python27

import sys
import subprocess

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

hdfs_root = sys.argv[1].rstrip('/')
partition_names = sys.argv[2].split(',')


def rename_from_root(root, partitions):
    if not partitions:
        return

    dir_lines = call('hdfs dfs -ls %s' % root)
    for line in dir_lines.split('\n'):
        parts = line.split()
        # skip lines without real file/dir data
        if len(parts) < 8:
            continue

        if line[0] == 'd':
            file_path = parts[-1]
            dir_name = file_path.split('/')[-1]
            prefix = file_path.rsplit(dir_name, 1)[0].rstrip('/')
            new_path = prefix + '/' + partitions[0] + '=' + dir_name
            call('hdfs dfs -mv %s %s' % (file_path, new_path))
            rename_from_root(new_path, partitions[1:])

rename_from_root(hdfs_root, partition_names)
