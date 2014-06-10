import os
from unipath import Path


class Resources(object):
    _base_path = '/tmp'

    def __init__(self, path=None):
        self._base_path = os.environ.get('RESOURCES_BASE_PATH',
                                         self._base_path)
        self.path = Path(self._base_path, path)

    def exists(self):
        return self.path.exists()

    def metadata(self, path=None):
        """ Returns a dictionary with info of all directories and files"""
        path = self.path if not path else path
        metadata = {
            'path': path.name,
            'contents': []
        }
        contents = metadata.get('contents')
        for subpath in path.listdir():
            if subpath.isdir():
                subpath_metadata = self.metadata(subpath)
            else:
                subpath_metadata = {'path': subpath.name}

            contents.append(subpath_metadata)

        return metadata

