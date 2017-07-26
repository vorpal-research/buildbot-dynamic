from twisted.web._auth.wrapper import UnauthorizedResource

from org.jetbrains.research.kotoed.buildbot.monkeys import twisted_UnauthorizedResource_render

UnauthorizedResource.render = twisted_UnauthorizedResource_render
