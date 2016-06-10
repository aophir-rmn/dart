import unittest
import jinja2
import os, sys, shutil
import filecmp
 
testfile = os.path.realpath(__file__)
testdir = os.path.dirname(testfile)
srcdir = '../vagrant_scripts'
sys.path.insert(0, os.path.abspath(os.path.join(testdir, srcdir)))
 
import deployment_generator as dg
 
 
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
              'vagrant_scripts_dir':testdir+'/vagrant_scripts',
              'docker_files_dir':testdir+'/docker_files'}

# The name of the folders for each container that docker-compose will launch (will have its own Dockerfile and config file, except postgres and elasticmq)
docker_compose_dirs= [paramaters['flask_webapp'], paramaters['engine_worker'], paramaters['trigger_worker'], paramaters['subscription_worker']]


class TestUM(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
      shutil.rmtree(testdir + "/docker_files/", ignore_errors=True)
      shutil.rmtree(testdir + "/vagrant_scripts/", ignore_errors=True)
      os.makedirs(testdir + "/docker_files/")
      os.makedirs(testdir + "/vagrant_scripts/")
      cls._templates_env = jinja2.Environment(loader=jinja2.FileSystemLoader([testdir + "/statics"]))
      dg.generate_dart_local_config(cls._templates_env, paramaters, docker_compose_dirs)


    @classmethod
    def tearDownClass(cls):
      shutil.rmtree(testdir + "/docker_files/", ignore_errors=True)
      shutil.rmtree(testdir + "/vagrant_scripts/", ignore_errors=True)
      print "Done"


    def setUp(self):
      pass


    def test_docker_compose(self):
        dg.generate_docker_compose_yaml(self._templates_env, paramaters)
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/docker-compose.yml", testdir + "/statics/gold_files/docker-compose.yml"))


    def test_additional_steps(self):
        dg.generate_additional_steps(self._templates_env, paramaters)
        self.assertTrue(filecmp.cmp(testdir + "/vagrant_scripts/additional_steps.sh", testdir + "/statics/gold_files/additional_steps.sh"))


    def test_web_worker(self):
        dg.generate_web_worker_dockerfile(self._templates_env, paramaters)
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/web/Dockerfile", testdir + "/statics/gold_files/web/Dockerfile"))
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/web/docker_CMD.sh", testdir + "/statics/gold_files/web/docker_CMD.sh"))
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/web/dart-local.yaml", testdir + "/statics/gold_files/web/dart-local.yaml"))


    def test_engine_worker(self):
        dg.generate_engine_worker_dockerfile(self._templates_env, paramaters)
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/engine/Dockerfile", testdir + "/statics/gold_files/engine/Dockerfile"))
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/engine/docker_CMD.sh", testdir + "/statics/gold_files/engine/docker_CMD.sh"))
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/engine/dart-local.yaml", testdir + "/statics/gold_files/engine/dart-local.yaml"))


    def test_trigger_worker(self):
        dg.generate_trigger_worker_dockerfile(self._templates_env, paramaters)
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/trigger/Dockerfile", testdir + "/statics/gold_files/trigger/Dockerfile"))
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/trigger/docker_CMD.sh", testdir + "/statics/gold_files/trigger/docker_CMD.sh"))
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/trigger/dart-local.yaml", testdir + "/statics/gold_files/trigger/dart-local.yaml"))


    def test_subscription_worker(self):
        dg.generate_subscription_worker_dockerfile(self._templates_env, paramaters)
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/subscription/Dockerfile", testdir + "/statics/gold_files/subscription/Dockerfile"))
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/subscription/docker_CMD.sh", testdir + "/statics/gold_files/subscription/docker_CMD.sh"))
        self.assertTrue(filecmp.cmp(testdir + "/docker_files/subscription/dart-local.yaml", testdir + "/statics/gold_files/subscription/dart-local.yaml"))


if __name__ == '__main__':
  unittest.main()
