import jinja2
import os
from vagrant_scripts import deployment_generator as dg

currentdir = os.path.dirname(os.path.realpath(__file__))

# The names of the container in docker-compose is how we access the container network.
# These values will populate the config files i(one per each container) as well.
paramaters = {'flask_webapp': 'web',
              'webapp_port': '5000',
              'database_container': 'postgres',
              'database_port': '5432',
              'sqs_container': 'elasticmq',
              'sqs_port': '9324',
              'engine_worker': 'engine',
              'trigger_worker': 'trigger',
              'subscription_worker': 'subscription',
              'synched_folder': '/vagrant_data/docker_files/',
              'docker_code_dir': '/tmp', # we need a folder that exists to override a docker-compose valoumes bug.
              'vagrant_code_dir':'/vagrant_data/dart',
              'vagrant_scripts_dir':currentdir+'/vagrant_scripts',
              'docker_files_dir':currentdir+'/docker_files'}

# The name of the folders for each container that docker-compose will launch (will have its own Dockerfile and config file, except postgres and elasticmq)
docker_compose_dirs= [paramaters['flask_webapp'], paramaters['engine_worker'], paramaters['trigger_worker'], paramaters['subscription_worker']]

if __name__ == "__main__":
  templates_env = jinja2.Environment(loader=jinja2.FileSystemLoader([currentdir + "/docker_files/templates"]))
  dg.generate_docker_compose_yaml(templates_env, paramaters)
  dg.generate_additional_steps(templates_env, paramaters)
  dg.generate_dart_local_config(templates_env, paramaters, docker_compose_dirs)  
  dg.generate_engine_worker_dockerfile(templates_env, paramaters)
  dg.generate_web_worker_dockerfile(templates_env, paramaters)
  dg.generate_trigger_worker_dockerfile(templates_env, paramaters)
  dg.generate_subscription_worker_dockerfile(templates_env, paramaters)
