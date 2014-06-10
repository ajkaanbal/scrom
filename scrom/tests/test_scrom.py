# -*- encoding: utf-8 -*-

import unittest
import os
import json

import mock

from paste.deploy.loadwsgi import appconfig
from sqlalchemy import engine_from_config
from sqlalchemy.orm import sessionmaker
from pyramid import testing

from scrom.models import DBSession, Project


here = os.path.dirname(__file__)
settings = appconfig('config:' + os.path.join(here, '../../', 'test.ini'))


class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = engine_from_config(settings)
        cls.Session = sessionmaker()

    def setUp(self):
        connection = self.engine.connect()

        self.transaction = connection.begin()

        DBSession.remove()
        DBSession.configure(bind=connection)
        self.session = self.Session(bind=connection)
        Project.session = self.session

    def tearDown(self):
        testing.tearDown()
        self.transaction.rollback()
        self.session.close()


class UnitTestBase(BaseTestCase):
    def setUp(self):
        self.config = testing.setUp(request=testing.DummyRequest())
        super(UnitTestBase, self).setUp()


class ProjectViewTests(UnitTestBase):
    def test_project_list_empty(self):
        from scrom.views import ProjectView
        request = testing.DummyRequest(path='/projects')

        view = ProjectView(request)
        project_list = view.collection_get()

        self.assertIn('projects', project_list)
        self.assertEqual(project_list.get('projects'), [])

    def test_project_list(self):
        from scrom.views import ProjectView
        request = testing.DummyRequest(path='/projects')

        self.session.add_all([
            Project(name='test_project_0'),
            Project(name='test_project_1')])
        self.session.flush()

        view = ProjectView(request)
        project_list = view.collection_get()

        project_list_expected = ['test_project_0', 'test_project_1']

        self.assertIn('projects', project_list)
        self.assertEqual(project_list.get('projects'), project_list_expected)

    def test_project_emtpy(self):
        from scrom.views import ProjectView
        request = testing.DummyRequest(path='/projects/test')
        request.matchdict = {'name': 'test'}

        self.session.add(Project(name='test'))
        self.session.flush()

        view = ProjectView(request)
        project = view.get()

        self.assertIn('name', project)
        self.assertIn('structure', project)
        self.assertEqual(project.get('name'), 'test')
        self.assertEqual(project.get('structure'), '')

    def test_project_notfound(self):
        from scrom.views import ProjectView
        from pyramid.exceptions import NotFound
        request = testing.DummyRequest(path='/projects/not_exist')
        request.matchdict = {'name': 'not_exist'}
        view = ProjectView(request)
        with self.assertRaises(NotFound):
            view.get()

    def test_project_structure(self):
        from scrom.views import ProjectView

        request = testing.DummyRequest(path='/projects/foo')
        request.matchdict = {'name': 'foo'}

        json_structure = """
        {"organizations": [{
            "organization": {
                "title": "folder_1",
                "item": {"title": "Item 1"}}
            },{
            "organization": {
                "title": "folder_2",
                "item": {"title": "Item 2"}}
            }]
        }
        """
        json_structure = json.loads(json_structure)
        self.session.add(Project(name='foo', structure=json_structure))
        self.session.flush()

        view = ProjectView(request)

        project = view.get()

        structure = project.get('structure')
        self.assertIn('organizations', structure)
        self.assertEqual(2, len(structure.get('organizations')))
        organization = structure.get('organizations')[0]
        self.assertIn('organization', organization)
        self.assertIn('title', organization.get('organization'))
        self.assertIn('item', organization.get('organization'))
        title = organization.get('organization').get('title')
        item = organization.get('organization').get('item')
        self.assertEqual(title, 'folder_1')
        self.assertIn('title', item)
        self.assertEqual('Item 1', item.get('title'))

    @mock.patch.dict('scrom.resources.os.environ',
                     {'RESOURCES_BASE_PATH': 'docs/fixtures'})
    def test_filesystem_based_project_structure(self):
        from scrom.views import ProjectView
        self.maxDiff = None

        request = testing.DummyRequest(path='/projects/foo')
        request.matchdict = {'name': 'foo'}
        request.json_body = ''

        structure_expected = {
            'path': 'foo',
            'contents': [
                {
                    'path': u'Tést test',
                    'contents': []
                },
                {
                    'path': 'assets',
                    'contents': [
                        {
                            'path': 'img.png'
                        }
                    ]
                },
                {'path': 'cap1.html'},
                {'path': 'cap2.html'},
                {'path': 'cap3.html'},
                {'path': 'cap4.html'},
                {'path': 'cap5.html'},
                {
                    'path': 'css',
                    'contents': [
                        {
                            'path': 'main.css'
                        }
                    ]
                },
                {
                    'path': 'js',
                    'contents': [
                        {
                            'path': 'main.js'
                        }
                    ]
                },
            ]
        }

        project = self.session.query(Project).filter_by(name='foo')
        self.assertEqual(0, project.count())

        view = ProjectView(request)
        view.post()

        projects = self.session.query(Project).filter_by(name='foo')
        self.assertEqual(1, projects.count())
        self.assertEqual(structure_expected, project.first().structure)


class ResourcesTests(unittest.TestCase):
    @mock.patch.dict('scrom.resources.os.environ',
                     {'RESOURCES_BASE_PATH': '/tmp'})
    @mock.patch('scrom.resources.Path')
    def test_base_path_on_environ(self, mock_resource_path):
        from scrom.resources import Resources

        Resources('inexistent_path')
        self.assertEqual('/tmp', os.environ.get('RESOURCES_BASE_PATH', ''))
        mock_resource_path.assert_called_with('/tmp', 'inexistent_path')

    @mock.patch.dict('scrom.resources.os.environ',
                     {'RESOURCES_BASE_PATH': ''})
    def test_path_non_empty(self):
        from scrom.resources import Resources
        self.maxDiff = None
        #  TODO: How to mock filesystem?
        resources = Resources('docs/fixtures/foo')
        metadata = resources.metadata()

        metadata_expected = {
            'path': 'foo',
            'contents': [
                {
                    'path': 'Tést test',
                    'contents': []
                },
                {
                    'path': 'assets',
                    'contents': [
                        {
                            'path': 'img.png'
                        }
                    ]
                },
                {'path': 'cap1.html'},
                {'path': 'cap2.html'},
                {'path': 'cap3.html'},
                {'path': 'cap4.html'},
                {'path': 'cap5.html'},
                {
                    'path': 'css',
                    'contents': [
                        {
                            'path': 'main.css'
                        }
                    ]
                },
                {
                    'path': 'js',
                    'contents': [
                        {
                            'path': 'main.js'
                        }
                    ]
                },
            ]
        }

        self.assertEqual(metadata_expected, metadata)
