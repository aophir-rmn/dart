import logging

from dart_manager.cli import dart_manager
from dart_manager.configure import configure
from dart_manager.manage import deploy, update


logging.VERBOSE = 15

def verbose(self, message, *args, **kws):
    if self.isEnabledFor(logging.VERBOSE):
        self._log(logging.VERBOSE, message, args, **kws)

logging.addLevelName(logging.VERBOSE, 'VERBOSE')
logging.Logger.verbose = verbose


class DartManagerError(Exception):
    pass
