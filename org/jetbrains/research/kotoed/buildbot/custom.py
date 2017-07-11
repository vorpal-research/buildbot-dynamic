import json
from os.path import isfile
from typing import Any, Dict, AnyStr

from buildbot.config import error
from buildbot.util.logger import Logger
from buildbot.util.service import BuildbotService
from buildbot.www.resource import Resource
from twisted.internet import defer
from twisted.internet.defer import Deferred
from twisted.web import http
from twisted.web.error import Error
from twisted.web.http import Request

ProjectList = Dict[AnyStr, Dict[AnyStr, Any]]


class BuildbotDynamicResourse(Resource):
    logger = Logger()

    def __init__(self, master, parent_service: "BuildbotDynamicService"):
        super().__init__(master)

        self.parent_service = parent_service

    def reconfigResource(self, new_config):
        pass

    def render_GET(self, request: Request):
        def cb(_):
            data = self.parent_service.get_projects()
            return defer.succeed(json.dumps(data).encode())

        return self.asyncRenderHelper(request, cb)

    def render_POST(self, request: Request):
        def cb(req):
            project_name = req.args.get(b'project_name')
            project_url = req.args.get(b'project_url')

            if project_name is None or project_url is None:
                raise Error(
                    http.BAD_REQUEST,
                    ("Missing some of 'project_name', 'project_url': (%s, %s)" % (project_name, project_url)).encode()
                )

            data = self.parent_service.add_project(
                project_name[0].decode(),
                project_url[0].decode()
            )
            return defer.succeed(json.dumps(data).encode())

        return self.asyncRenderHelper(request, cb)


class BuildbotDynamicService(BuildbotService):
    logger = Logger()

    name = "Buildbot Dynamic Service"

    project_list_storage_key = "project_list_storage"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.project_list_storage = None

    def reconfigService(self, *args, **kwargs) -> Deferred:
        root = self.master.www.apps.get("base").resource
        root.putChild(
            b'custom', BuildbotDynamicResourse(self.master, self)
        )

        self.project_list_storage = kwargs[self.project_list_storage_key]

        return super().reconfigService(self.name, *args, **kwargs)

    def checkConfig(self, *args, **kwargs) -> None:
        super().checkConfig(BuildbotDynamicService.name, *args, **kwargs)

        if self.project_list_storage_key not in kwargs:
            error("No 'project_list_storage' set for BuildbotDynamicService")

        if not isfile(kwargs[self.project_list_storage_key]):
            error("File '%s' does not exist" % kwargs[self.project_list_storage_key])

    def add_project(self, project_name: AnyStr, project_url: AnyStr) -> ProjectList:
        projects = self.get_projects()

        if project_name in projects:
            raise DuplicateProjectException(
                "Project '%s' already exists in: %s" % (project_name, projects)
            )

        new_project = {
            project_name: {
                "url": project_url
            }
        }

        projects.update(new_project)

        with open(self.project_list_storage, "wt") as f:
            json.dump(projects, f)

        return projects

    def get_projects(self) -> ProjectList:
        with open(self.project_list_storage, "rt") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                self.logger.error("Error when decoding '%s': %s" % (self.project_list_storage, e.msg))
                data = {}
        return data


class DuplicateProjectException(Error):
    def __init__(self, *args: Any) -> None:
        super().__init__(http.BAD_REQUEST, *args)
