import re
from dart.model.action import Action
import logging

_logger = logging.getLogger(__name__)


class AWS_Batch_Dag(object):
    def __init__(self, config_metadata, client, s3_client):
        self.job_definition = config_metadata(['aws_batch', 'job_definition']) # TODO: remove - we should use the action.data.engine_name value
        self.job_definition_suffix = config_metadata(['aws_batch', 'job_definition_suffix']) # to discern between prd/stg images
        self.job_queue = config_metadata(['aws_batch', 'job_queue'])

        # Where to place inputs/outputs to action from/to actions.  We will use the workflow_instance as "sub-bucket"
        self.s3_input_output = config_metadata(['aws_batch', 's3_input_output'])
        self.sns_arn = config_metadata(['aws_batch', 'sns_arn'])  # SNS to notify workflow completion and action completion

        _logger.info("AWS_Batch: using job_definition={0} and job_queue={1}".format(self.job_definition, self.job_queue))
        self.client = client
        self.s3_client = s3_client


    def generate_job_name(self, workflow_id, order_idx, action_name):
        """ Names should not exceed 50 characters or else cloudwatch logs will fail. """
        job_name = "{0}_{1}_{2}".format(workflow_id, order_idx, action_name.replace("-", "_"))
        valid_characters_name = re.sub('[^a-zA-Z0-9_]', '', job_name) # job name valid pattern is: [^a-zA-Z0-9_]
        return valid_characters_name[0:50]


    def cancel_previous_jobs(self, previous_jobs, reason="Failed to create all jobs in a dag"):
        for idx, job_id in enumerate(previous_jobs):
            response = None
            try:
                response = self.client.cancel_job(jobId=job_id, reason=reason)
            except Exception as err:
                _logger.error("Failed to cancel job={0} {1}/{2} jobs. err:{3}".format(job_id, idx, len(previous_jobs), err))

            _logger.info("Canceling job #{0}={1}. metadata={2}".format(idx, job_id, response))


    def get_latest_active_job_definition(self, job_def_name):
        """ E.g.  job_def_name='redshift_engine' ==> we will get redshift_engine:3 (if 3 is the latest active version).
                  This will allow us to update the version used without changing the yaml files.
            Note: It is implicitly assumed that the AWS Batch job definitions are named the same as the engine names in dart.
        """
        job_name = "{0}_{1}".format(job_def_name, self.job_definition_suffix) # e.g. s3_engine_prd, or redshift_engine_stg
        _logger.info("AWS_batch: searching latest active job definition for name={0}".format(job_name))
        response = self.client.describe_job_definitions(jobDefinitionName=job_name, status='ACTIVE')
        _logger.info("AWS_batch: len(response['jobDefinitions'])={0}".format(len(response['jobDefinitions'])))
        arr = sorted(response['jobDefinitions'],
                     key=lambda x: int(x['revision']))  # the last item will be the highest (last) revision
        return arr[-1]['jobDefinitionArn']


    def get_worflow_attributes(self, first_action):
        try:
            wf_attribs = {
                "user_id": first_action.data.user_id,
                "workflow_id": first_action.data.workflow_id,
                "workflow_instance_id": first_action.data.workflow_instance_id, # will use to update status of wf in last action
                "datastore_id": first_action.data.datastore_id,
                "update_db_sns": self.sns_arn
            }
        _logger.info("AWS_Batch: building workflow attributes {0}".format(wf_attribs))
        return wf_attribs
        except Exception as err:
            _logger.error("AWS_Batch: failed to extract data from first action in workflow {0}, err={1}".format(first_action, err))
            raise ValueError("AWS_Batch: failed to extract data from first action in workflow {0}, err={1}".format(first_action, err))


    # is_first_action/is_last_action in the workflow.  We notify upon start an end of workflow to update db status
    # wf_attribs - dictionary of action data that will be handy to have on hand without queryig db and fir workflow identification
    # action_env - dictionary of variable we need to run the actions
    def generate_env_vars(self, wf_attribs, action_env, is_first_action=False, is_last_action=False):
        wf_attribs_data = [{'name': name, 'value': value} for name,value in wf_attribs.iteritems()]
        action_env_data = [{'name': name, 'value': value} for name,value in action_env.iteritems()]

        env = wf_attribs_data.extend(action_env_data)
        env.append({'name': 'is_first_action', 'value': is_first_action})
        env.append({'name': 'is_last_action', 'value': is_last_action})

        _logger.info("AWS_Batch: creating environment variables {0} for workflow={1}, action={0}".
                     format(env, wf_attribs['workflow_id'], action_env['']))
        return env


    # The bucket is self.s3_input_output/workflow_instance_id and the first file is named <wf_instance-id>.dat
    # and its content is filled with json_input (if any)
    def create_s3_bucket_for_workflow_io(self, workflow_instance_id, json_input=''):
        try:
            response_bucket = self.s3_client.create_bucket(
                ACL='public-read-write',
                Bucket="{0}/{1}".format(self.s3_input_output, workflow_instance_id),  # The bucket unique to this workflow
                CreateBucketConfiguration={'LocationConstraint': 'us-east-1'} # to ensure read after write files need to be in same region
            )
            _logger.info("AWS_Batch: created bucket for workflow {0}, {1}".format(workflow_instance_id, response_bucket))

            # first input to first action. Rest of read/write to s3 is handled from within the actions.
            response_key = self.s3_client.put_object(
                ACL='public-read-write',
                Body=json_input,
                Bucket="{0}/{1}".format(self.s3_input_output, workflow_instance_id),  # The bucket unique to this workflow
                Key=workflow_instance_id
            )
            _logger.info("AWS_Batch: created input 'file' for workflow {0}, {1}, with input={2}".
                         format(workflow_instance_id, response_key, json_input))
        except Exception as err:
            _logger.error("AWS_Batch: S3 failed for workflow. base={0} , workflow_instance_id={1}, err: {2}".format(
                self.s3_input_output, workflow_instance_id, err))


    def generate_dag(self, ordered_actions, retries_on_failures):
        if not ordered_actions or not all(isinstance(x, Action) for x in ordered_actions):
            raise ValueError('Must receive actions in order to build a DAG. action={0}'.format(ordered_actions))

        # This info will be sent to each job env and is mostly used for identifying workflows when querying batch
        # and reduce the need to query the database.  This is effectively a mapping between job-id to action-id
        # and we also know the workflow_instance_id (that needs to be updated)
        wf_attribs = self.get_worflow_attributes(ordered_actions[0])
        wf_attribs['retries_on_failures'] = retries_on_failures
        workflow_id = wf_attribs['workflow_id']
        _logger.info("AWS_Batch: generate_dag, #actions={0}, datastore={1}, workflow={2}, workflow_instance={3}".
                     format(len(ordered_actions), wf_attribs['datastore_id'], workflow_id, wf_attribs['workflow_instance_id']))

        self.create_s3_bucket_for_workflow_io(wf_attribs['workflow_instance_id'])

        previous_jobs = []  # will hold an array of jobIds, one per each action placed in Batch
        last_action_index = len(ordered_actions)-1
        for idx, oaction in enumerate(ordered_actions):

            action_env = {
                "current_step_id": oaction.data.workflow_action_id,  # the action template this action was created of
                "is_continue_on_failure": (oaction.data.on_failure == "CONTINUE"),
                "ACTION_ID": oaction.id,
                "s3_input_key": wf_attribs['workflow_instance_id']
            }

            cmd = ["echo", str(oaction.data.order_idx)]

            dependency = []
            if previous_jobs:
                dependency = [{'jobId': previous_jobs[-1]}]

            response = {'jobId': None}
            try:
                job_name = self.generate_job_name(workflow_id, oaction.data.order_idx, oaction.data.name)
                _logger.info("AWS_Batch: job-name={0}, dependsOn={1}, cmd={2}".format(job_name, dependency, cmd))

                response = self.client.submit_job(jobName=job_name,
                                                  jobDefinition=self.get_latest_active_job_definition('awscli'), # TODO: replace with oaction.data.engine_name
                                                  jobQueue=self.job_queue,
                                                  containerOverrides={
                                                      'command': cmd,
                                                      'environment': self.generate_env_vars(wf_attribs,
                                                                                            action_env,
                                                                                            idx == 0,
                                                                                            idx == last_action_index)
                                                  })
                _logger.info("AWS_Batch: response={0}".format(response))

                previous_jobs.append(response['jobId'])
            except Exception as err:
                _logger.error("AWS_Batch: DAG-err={0}".format(err))
                self.cancel_previous_jobs(previous_jobs)
                raise

        _logger.info("AWS_Batch: Done building workflow {0}".format(workflow_id))

