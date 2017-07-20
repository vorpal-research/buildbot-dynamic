import json
from collections import namedtuple
from hashlib import sha512
from os.path import isfile
from typing import Any, Dict, AnyStr, Callable

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

Project = namedtuple("Project", ['name', 'url', 'type'])


def name2sha512(name: AnyStr) -> AnyStr:
    return sha512(name.encode()).hexdigest()[0:32]


class BuildbotDynamicResourse(Resource):
    logger = Logger()

    def __init__(self, master, parent_service: "BuildbotDynamicService"):
        super().__init__(master)

        self.parent_service = parent_service

    def reconfigResource(self, new_config):
        pass

    # TODO: add self.master.www.assertUserAllowed(...)

    def render_GET(self, request: Request):
        def cb(_):
            data = self.parent_service.get_projects()
            return defer.succeed(json.dumps(data).encode())

        return self.asyncRenderHelper(request, cb)

    def render_POST(self, request: Request):
        def cb(req):
            param_names = Project._fields

            params = [req.args.get(pname.encode()) for pname in param_names]

            if any([param is None for param in params]):
                raise Error(
                    http.BAD_REQUEST,
                    ("Missing some of %s: %s" % (param_names, params)).encode()
                )

            data = self.parent_service.add_project(
                Project._make([param[0].decode() for param in params])
            )
            return defer.succeed(json.dumps(data).encode())

        return self.asyncRenderHelper(request, cb)


class BuildbotDynamicService(BuildbotService):
    logger = Logger()

    name = "Buildbot Dynamic Service"

    course_name_key = "course_name"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.course_name = None
        self.course_name_sha512 = None
        self.project_list_storage = None

    def reconfigService(self, *args, **kwargs) -> Deferred:
        self.course_name = kwargs[self.course_name_key]
        self.course_name_sha512 = name2sha512(self.course_name)
        self.project_list_storage = "%s.json" % self.course_name_sha512

        root = self.master.www.apps.get("base").resource
        root.putChild(
            self.course_name_sha512.encode(), BuildbotDynamicResourse(self.master, self)
        )

        return super().reconfigService(self.name, *args, **kwargs)

    def checkConfig(self, *args, **kwargs) -> None:
        super().checkConfig(BuildbotDynamicService.name, *args, **kwargs)

        if self.course_name_key not in kwargs:
            error("No 'course_name' set for BuildbotDynamicService")

        course_name = kwargs[self.course_name_key]
        course_name_sha512 = name2sha512(course_name)
        project_list_storage = "%s.json" % course_name_sha512

        if not isfile(project_list_storage):
            error("File '%s' does not exist" % project_list_storage)

    def add_project(self, project: Project) -> ProjectList:
        projects = self.get_projects()

        if project.name in projects:
            raise DuplicateProjectException(
                "Project '%s' already exists in: %s" % (project.name, projects)
            )

        new_project = {
            project.name: {
                "name": project.name,
                "url": project.url,
                "type": project.type
            }
        }

        projects.update(new_project)

        with open(self.project_list_storage, "wt") as f:
            json.dump(projects, f)

        self.master.reconfig()

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


def load_dynamic_projects(course_name: AnyStr, cb: Callable[[Project], None]):
    course_name_sha512 = name2sha512(course_name)
    project_list_file = "%s.json" % course_name_sha512

    with open(project_list_file, "rt") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    for (name, project) in data.items():
        if any([e is None for e in project]):
            error("Project '%s' misses one of the required properties" % project)
        cb(name, Project(**project))
