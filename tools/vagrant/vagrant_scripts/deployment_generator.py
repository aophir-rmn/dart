import os

def render_dart_template(paramaters, template, container_cmd="", work_dir="/", dart_role="web", additional_run_steps=[], export_port=""):
  result = template.render(flask_webapp=paramaters['flask_webapp'],
                           webapp_port=paramaters['webapp_port'],
                           database_container=paramaters['database_container'], 
                           database_port=paramaters['database_port'],
                           sqs_container=paramaters['sqs_container'],
                           sqs_port=paramaters['sqs_port'],
                           engine_worker=paramaters['engine_worker'],
                           trigger_worker=paramaters['trigger_worker'],
                           subscription_worker=paramaters['subscription_worker'],
                           synched_folder=paramaters['synched_folder'],
                           docker_code_dir=paramaters['docker_code_dir'],
                           vagrant_code_dir=paramaters['vagrant_code_dir'],
                           export_port=export_port,
                           container_cmd=container_cmd,
                           additional_run_steps=additional_run_steps,
                           container_work_dir=work_dir,
                           container_dart_role=dart_role)
  return result


def generate_docker_compose_yaml(env, params):
  docker_compose_template = env.get_template("docker-compose.yml.template") 
  docker_compose_result = render_dart_template(params, docker_compose_template)

  # Write the docker-compose file we will use to launch  container with.
  with open(params['docker_files_dir'] + "/docker-compose.yml", "wb") as fh:
    fh.write(docker_compose_result)


def generate_additional_steps(env, params):
  additional_steps_template = env.get_template("additional_steps.sh.template") 
  additional_steps_result = render_dart_template(params, additional_steps_template)

  with open(params['vagrant_scripts_dir'] + "/additional_steps.sh", "wb") as fh:
    fh.write(additional_steps_result)


def generate_dart_local_config(env, params, dirs):
  dart_local_config_template = env.get_template("dart-local.yaml.template") 
  dart_local_config_result = render_dart_template(params, dart_local_config_template)

  # Write dart-local.yaml to every folder of a docker container 
  for dir in dirs:
    if not os.path.exists("./docker_files/"+dir):
      os.makedirs(params['docker_files_dir'] + "/" + dir)
    with open(params['docker_files_dir'] + "/" + dir + "/dart-local.yaml", "wb") as fh:
      fh.write(dart_local_config_result)


def generate_worker(env, params, cmd, role, work_directory, worker_name, port="", run_steps=[]):
  dockerfile_template = env.get_template("Dockerfile.template") 
  dockerCMD_template = env.get_template("docker_CMD.sh.template") 

  dockerfile_result = render_dart_template(paramaters=params,
      template=dockerfile_template,
      container_cmd=cmd,
      dart_role=role,
      export_port=port,
      additional_run_steps=run_steps,
      work_dir=work_directory)
  with open(params['docker_files_dir'] + "/" + params[worker_name]  + "/Dockerfile", "wb") as fh:
    fh.write(dockerfile_result)

  dockerCMD_result = render_dart_template(paramaters=params,
      template=dockerCMD_template,
      container_cmd=cmd,
      dart_role=role,
      export_port=port,
      additional_run_steps=run_steps,
      work_dir=work_directory)
  with open(params['docker_files_dir'] + "/" + params[worker_name]  + "/docker_CMD.sh", "wb") as fh:
    fh.write(dockerCMD_result)


def generate_engine_worker_dockerfile(env, params):
  generate_worker(env=env,
                  params=params,
                  cmd="python ./engine.py", 
                  role="worker",
                  work_directory=params['docker_code_dir']+"/src/python/dart/worker",
                  worker_name='engine_worker')


def generate_web_worker_dockerfile(env, params):
  generate_worker(env=env,
                  params=params,
                  cmd="python ./server.py", 
                  role="web",
                  work_directory=params['docker_code_dir']+"/src/python/dart/web",
                  port="EXPOSE 5000",
                  run_steps=["npm install bower -g", "cd " + params['docker_code_dir'] + "/src/python/dart/web/ui && bower install --allow-root"],
                  worker_name='flask_webapp')


def generate_trigger_worker_dockerfile(env, params):
  generate_worker(env=env,
                  params=params,
                  cmd="python ./trigger.py", 
                  role="web",
                  work_directory=params['docker_code_dir'] + "/src/python/dart/worker",
                  worker_name='trigger_worker')


def generate_subscription_worker_dockerfile(env, params):
  generate_worker(env=env,
                  params=params,
                  cmd="python ./subscription.py", 
                  role="web",
                  work_directory=params['docker_code_dir'] + "/src/python/dart/worker",
                  worker_name='subscription_worker')

