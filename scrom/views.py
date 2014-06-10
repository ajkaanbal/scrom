
from pyramid.view import view_config
from pyramid.exceptions import NotFound

from cornice.resource import resource

from .models import (
    DBSession,
    Project,
    )
from .resources import Resources


@view_config(route_name='home', renderer='templates/mytemplate.pt')
def home(request):
    return {'project': 'SCROM'}


@resource(collection_path='/projects', path='/projects/{name}')
class ProjectView(object):
    def __init__(self, request):
        self.request = request

    def collection_get(self):
        """ Return the list of all projects """
        projects = DBSession.query(Project).all()
        return {
            'projects': [project.name for project in projects]
        }

    def get(self):
        project_name = self.request.matchdict.get('name')
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

        if project_name:
            projects = DBSession.query(Project).filter_by(name=project_name)
            if not projects.first():
                resources = Resources(project_name)
                structure = resources.metadata()
                project = Project(name=project_name, structure=structure)
                DBSession.add(project)
                DBSession.flush()
            else:
                # project_query.update({'structure': structure})
                project = projects.first()
                DBSession.add(project)

            return {'project_id': project.uid}
