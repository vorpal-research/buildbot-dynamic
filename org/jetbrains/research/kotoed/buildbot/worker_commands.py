import glob
import os

from buildbot_worker.commands import base
from twisted.python import log


class RecursiveGlobPath(base.Command):
    header = "glob-rec"

    # args['path'] is relative to Builder directory, and is required.
    requiredArgs = ['path']

    def start(self):
        pathname = os.path.join(self.builder.basedir, self.args['path'])

        try:
            files = glob.glob(pathname, recursive=True)
            self.sendStatus({'files': files})
            self.sendStatus({'rc': 0})
        except OSError as e:
            log.msg("GlobPath %s failed" % pathname, e)
            self.sendStatus(
                {'header': '%s: %s: %s' % (self.header, e.strerror, pathname)})
            self.sendStatus({'rc': e.errno})
