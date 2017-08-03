from typing import AnyStr

from buildbot.process.buildstep import BuildStep, ShellMixin
from buildbot.process.results import SUCCESS
from buildbot.steps.source.git import Git
from buildbot.steps.source.mercurial import Mercurial
from buildbot.steps.worker import CompositeStepMixin
from twisted.internet import defer
from twisted.logger import Logger


class VCS:
    logger = Logger()

    name = "VCS"

    def __new__(cls, **kwargs):
        vcs_type: AnyStr = kwargs.get("vcs_type")
        kwargs.pop("vcs_type")

        if "git" == vcs_type:
            __impl = Git(**kwargs)
        elif "hg" == vcs_type or "mercurial" == vcs_type:
            __impl = Mercurial(**kwargs)
        else:
            raise NotImplementedError(f"VCS step does not support type '{vcs_type}'")

        return __impl


class PlainTextResults(BuildStep, ShellMixin, CompositeStepMixin):
    logger = Logger()

    def __init__(self, file_name_template: AnyStr, **kwargs):
        super().__init__(**kwargs)

        self.name = f"Plain text results for <{file_name_template}>"

        self.file_name_template = file_name_template

    def start(self):
        pass

    def runGlobRec(self, path, **kwargs):
        """ find files matching a shell-style pattern (recursively)"""

        def commandComplete(cmd):
            return cmd.updates['files'][-1]

        return self.runRemoteCommand('glob-rec', {'path': path, 'logEnviron': self.logEnviron},
                                     evaluateCommand=commandComplete, **kwargs)

    @defer.inlineCallbacks
    def run(self):
        files = yield self.runGlobRec(self.file_name_template)

        for file in files:
            content = yield self.getFileContentFromWorker(file)

            yield self.addCompleteLog(file, content)

        defer.returnValue(SUCCESS)
