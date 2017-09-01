from buildbot.scripts.logwatcher import LogWatcher as MasterLogWatcher
from buildbot_worker.scripts.logwatcher import LogWatcher as WorkerLogWatcher
from twisted.web._auth.wrapper import UnauthorizedResource

from org.jetbrains.research.kotoed.buildbot.monkeys import twisted_UnauthorizedResource_render, correct_ident_re

# Fix quoting
UnauthorizedResource.render = twisted_UnauthorizedResource_render

# Fix too strict identifiers
# identifiers.ident_re = correct_ident_re

# Fix startup delay
MasterLogWatcher.TIMEOUT_DELAY = 30.0
WorkerLogWatcher.TIMEOUT_DELAY = 30.0
