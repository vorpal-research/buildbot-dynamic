from buildbot.scripts.logwatcher import LogWatcher
from twisted.web._auth.wrapper import UnauthorizedResource

from org.jetbrains.research.kotoed.buildbot.monkeys import twisted_UnauthorizedResource_render, correct_ident_re

# Fix quoting
UnauthorizedResource.render = twisted_UnauthorizedResource_render

# Fix too strict identifiers
# identifiers.ident_re = correct_ident_re

# Fix startup delay
LogWatcher.TIMEOUT_DELAY = 30.0
