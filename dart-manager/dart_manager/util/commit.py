import re

from dart_manager.util.util import lazyproperty
from git import Repo
import tempfile





class DartCommit(object):

    _hash_re = re.compile(r'^[0-9a-f]{40}$')

    def __init__(self, ref, clone_path):
        self.ref = ref
        self.cl
        if not DartCommit.is_valid_ref(self.ref):
            raise '"{}" is not a valid commit reference.'.format(ref)

    @lazyproperty
    def repo(self, path):
        return Repo.clone_from(DART_REPO_URL, self.dir_path)  # todo: progress

    @staticmethod
    def is_valid_ref(ref):
        return DartCommit._hash_re.match(ref)