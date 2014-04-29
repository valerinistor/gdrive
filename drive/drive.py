from apiclient import errors
from filewatcher  import FileWatcher
from drivefile import GoogleDriveFile
import os

class GoogleDrive:

    def __init__(self, root_folder, service):
        self.service = service
        self.root_folder = root_folder
        self.drive_files = {}

    def synchronize_drive(self):
        shared_folder = os.path.join(self.root_folder, 'SharedWithMe')
        trash_folder = os.path.join(self.root_folder, 'Trash')

        # synchronize drive files
        self._synchronize_files('root', self.root_folder, query='not trashed')
        # synchronize shared files
        self._synchronize_files_by_type(shared_folder, 'sharedWithMe')
        # synchronize trashed files
        self._synchronize_files_by_type(trash_folder, "trashed and 'root' in parents")

        # start watching files for changes
        watcher = FileWatcher(self, self.root_folder)
        watcher.start()

        try:
            while watcher.is_alive():
                watcher.join(1)
        except (KeyboardInterrupt, SystemExit):
            print 'Shutting down ...'
            watcher.request_stop()

    def _synchronize_files(self, root_id, root_path, query=None):
        self._create_local_dir(root_path)
        children = self._list_children(folderId=root_id, query=query)

        for child in children:
            item = self._get_file(child['id'])
            path = os.path.join(root_path, item['title'])

            if item['mimeType'] == 'application/vnd.google-apps.folder':
                self._synchronize_files(item['id'], path, query)
            else:
                if item.has_key('downloadUrl'):
                    drive_file = GoogleDriveFile(self.service, path, item)
                    self.drive_files[path] = drive_file
                    drive_file.download_from_url()

    def _synchronize_files_by_type(self, root_path, query):
        self._create_local_dir(root_path)
        items = self._list_file(query=query)

        for item in items:
            path = os.path.join(root_path, item['title'])
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                self._synchronize_files(item['id'], path)
            if item.has_key('downloadUrl'):
                drive_file = GoogleDriveFile(self.service, path, item)
                self.drive_files[path] = drive_file
                drive_file.download_from_url()

    def _list_file(self, query=None):
        try:
            return self.service.files().list(q=query).execute()['items']
        except errors.HttpError, error:
            print 'An error occurred: %s' % error

    def _list_children(self, folderId, query=None):
        items = []
        try:
            items = self.service.children().list(q=query, folderId=folderId).execute()['items']
        except errors.HttpError, error:
            print 'An error occurred: %s' % error
        return items

    def _get_file(self, file_id):
        try:
            return self.service.files().get(fileId=file_id).execute()
        except errors.HttpError, error:
            print 'An error occurred: %s' % error

    def on_delete(self, path):
        print 'deleted   %s' % path
        self.drive_files[path].trash()

    def on_modified(self, path):
        print 'modified  %s' % path

    def on_create(self, path):
        print 'created   %s' % path

    def _create_local_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
