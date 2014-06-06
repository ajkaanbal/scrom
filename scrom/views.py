import json

from pyramid.view import view_config
from pyramid.exceptions import NotFound

from unipath import Path
from cornice.resource import resource

from .models import (
    DBSession,
    Project,
    )


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def home(request):
    return {'project': 'SCROM'}


@resource(collection_path='/projects', path='/projects/{name}')
class ProjectView(object):
    def __init__(self, request):
        self.request = request
        # path = self.request.registry.settings['media']
        # self.path = Path(path)

    def collection_get(self):
        """ Return the list of all projects """
        # projects = [file.name for file in self.path.listdir() if file.isdir()]
        projects = DBSession.query(Project).all()
        return {
            'projects': [project.name for project in projects]
        }

    def get(self):
        project_name = self.request.matchdict.get('name')
        # project = self.path.child(project_name)
        # project_files = [f.name for f in project.listdir() if f.ext == '.html']
        # return {project_name: project_files}
        project = DBSession.query(Project).filter_by(name=project_name).first()
        if not project:
            raise NotFound('Project {0} does not found'.format(project_name))

        return {
            'name': project.name,
            'structure': project.structure or ''
        }

    def post(self):
        project_name = self.request.matchdict.get('name')
        structure = self.request.json_body

        if project_name and structure:
            project_query = DBSession.query(Project).filter_by(name=project_name)
            if not project_query.first():
                project = Project(name=project_name, structure=structure)
                DBSession.add(project)
            else:
                # project_query.update({'structure': structure})
                project = project_query.first()
                DBSession.add(project)
            return {'project': project.structure}


