import click
from git import Repo
from dart_manager.cli import dart_manager


DART_REPO_URL = 'https://github.com/RetailMeNotSandbox/dart.git'


class ManagementSession(Session):

    def __init__(self):
        super(ManagementSession, self).__init__()
        self.resources = None
        self.env = None

    def use_resources(self, resources_path):
        try:
            self.resources = DartResources(resources_path)
        except Exception as e:
            message = 'Error loading dart-resources:\n{}'.format(e.message)
            raise click.UsageError(message)

    def use_env(self, env_name):
        if env_name not in self.resources.envs:
            message = 'Could not find "{}" env in dart-resources'.format(env_name)
            raise click.UsageError(message)

        self.env = self.resources.envs[env_name]


    def use_commit(self, commit_ref):
        pass


# resources option


@callback
def process_resources_option(session, resources_path):
    resources_path = resources_path or session.config.resources_path
    if not resources_path:
        message = 'No dart-resources path set; either configure dart-manager or use --resources option.'
        raise click.UsageError(message)

    session.use_resources(resources_path)


resources_option = click.option(
    '--resources',
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help='The absolute path to your dart_resources directory.',
    is_eager=True,  # process before env argument
    callback=process_resources_option,
)


# env argument


@callback
def process_env_argument(session, env_name):
    session.set_active_env(env_name)


env_argument = click.argument('env',  callback=process_env_argument)


# commit argument


class CommitParamType(click.ParamType):
    name = 'commit'

    def convert(self, value, param, ctx):
        repo = Repo.clone_from(DART_REPO_URL, self.dir_path)

        self.fail('"{}" is not a valid commit reference.'.format(value), param, ctx)


COMMIT_TYPE = CommitParamType()


@callback
def process_commit_argument(session, commit):
    session.set_commit(commit)


commit_argument = click.argument('commit', type=COMMIT_TYPE, callback=process_commit_argument)


# commands



