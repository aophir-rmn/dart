import tempfile
from functools import wraps

import click
import click_log
import logging

from dart_manager.configure import DartManagerConfig
from dart_manager.util.util import lazyproperty


class Session(object):
    """Holds data for a dart-manager session.

    Used to pass data between nested click contexts. I use 'session' to
    reference a single dart-manager command invocation, such as:
    `$ dart-manager deploy update prod master`

    """

    @lazyproperty
    def working_dirpath(self):
        """Path of temp directory for all disk storage during this session."""
        return tempfile.mkdtemp(prefix='dart')

    # @classmethod
    # def store_param_value(cls, ctx, param, value):
    #     session = ctx.ensure_object(cls)

    @staticmethod
    def callback(func):
        """Decorates function to be used as a click command callback."""
        @wraps(func)
        def wrapper(ctx, param, value):
            session = ctx.ensure_object(Session)
            return ctx.invoke(f, session, value)

        return new_callback

@callback
def process_verbosity_argument(session, verbosity):
    print(verbosity)
    if verbosity > 2:
        raise click.BadParameter('Only two verbosity levels are supported', param_hint='verbosity')


@click.group()
@click_log.init(__name__)
@click.option(
    '--resources', '-r',
    env_var='DART_RESOURCES',
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help='The absolute path to your dart-resources directory.',
)
@click.option(
    '--verbose', '-v',
    count=True,
    help='Can be passed up to 2 times.',
    callback=Session.set_verbosity,
    expose_value=False,
)
def dart_manager(verbosity):
    click_log.set_level({
        0: logging.INFO,
        1: logging.VERBOSE,
        2: logging.DEBUG,
    }.get(verbosity))


@dart_manager.group()
@click.argument('env')
@click.argument('commit')
def deploy():
    pass


@deploy.command()
@click.option(
    '--create-core',
    is_flag=True,
)
@click.option(
    '--dart-tag',
    help='A tag that identifies AWS resources as part of Dart.',
    default='dart',
)
def deploy():
    """Creates the resources"""
    pass


@deploy.group()
def update():
    pass


@dart_manager.command()
def rollback():
    pass