from pyramid.response import Response
from pyramid.view import view_config

from sqlalchemy.exc import DBAPIError

from unipath import Path
from cornice import Service
from cornice.resource import resource

from .models import (
    DBSession,
    MyModel,
    )


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def home(request):
    return {'project': 'SCROM'}


@resource(collection_path='/projects', path='/projects/{name}')
class Project(object):
    def __init__(self, request):
        self.request = request
        path = self.request.registry.settings['media']
        self.path = Path(path)

    def collection_get(self):
        """ Return the list of all projects """
        projects = [file.name for file in self.path.listdir() if file.isdir()]
        return {
            'projects': projects
            }

    def get(self):
        project_name = self.request.matchdict.get('name')
        project = self.path.child(project_name)
        project_files = [f.name for f in project.listdir() if f.ext == '.html']
        return {project_name: project_files}

