from typing import AnyStr

from buildbot.steps.source.git import Git
from buildbot.steps.source.mercurial import Mercurial
from twisted.logger import Logger


class VCS:
    logger = Logger()

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
