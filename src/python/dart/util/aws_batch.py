import re
from dart.model.action import Action
import logging

_logger = logging.getLogger(__name__)


class AWS_Batch_Dag(object):
    def __init__(self, config_metadata, client):
        self.job_definition = config_metadata(['aws_batch', 'job_definition'])
        self.job_queue = config_metadata(['aws_batch', 'job_queue'])
        self.client = client

    def generate_job_name(self, workflow_id, order_idx, action_name):
        job_name = "{0}_{1}_{2}".format(workflow_id, order_idx, action_name.replace("-", "_"))
        return re.sub('[^a-zA-Z0-9_]', '', job_name) # job name valid pattern is: [^a-zA-Z0-9_]

    def cancel_previous_jobs(self, previous_jobs, reason="Failed to create all jobs in a dag"):
        for idx, job_id in enumerate(previous_jobs):
            response = None
            try:
                response = self.client.cancel_job(jobId=job_id, reason=reason)
            except Exception as err:
                _logger.error("Failed to cancel job={0} {1}/{2} jobs. err:{3}".format(job_id, idx, len(previous_jobs), err))

            _logger.info("Canceling job #{0}={1}. metadata={2}".format(idx, job_id, response))

    def generate_dag(self, ordered_actions, workflow_id):
        if not ordered_actions or not all(isinstance(x, Action) for x in ordered_actions):
            raise ValueError('Must receive actions in order to build a DAG. action={0}'.format(ordered_actions))

        previous_jobs = [] # will hold an array of jobIds, one per each action placed in Batch
        for oaction in ordered_actions:
            cmd = ["echo", str(oaction.data.order_idx)]
            dependency = []
            if previous_jobs:
                dependency = [{'jobId': previous_jobs[-1]}]

            response = {'jobId': None}
            try:
                response = self.client.submit_job(jobName=self.generate_job_name(workflow_id,
                                                                                 oaction.data.order_idx,
                                                                                 oaction.data.name),
                                                  dependsOn=dependency,
                                                  jobDefinition=self.job_definition,
                                                  jobQueue=self.job_queue,
                                                  containerOverrides={'command': cmd})
                previous_jobs.append(response['jobId'])
                _logger.info("============= {0}".format(response))
            except Exception as err:
                _logger.error("====== err={0}".format(err))
                self.cancel_previous_jobs(previous_jobs)
                raise

