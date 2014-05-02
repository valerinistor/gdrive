from apiclient import errors
from filewatcher  import FileWatcher
from drivefile import GoogleDriveFile
from drivefile import folder_mime_type
import os
import time

class GoogleDrive:

    def __init__(self, root_folder, service):
        self.service = service
        self.root_folder = root_folder
        self.drive_files = {}
        root_metadata = {'id': 'root'}
        self.drive_files[self.root_folder] = GoogleDriveFile(service, root_folder, root_metadata)

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
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            print 'Shutting down ...'
            watcher.stop()
        watcher.join()

    def _synchronize_files(self, root_id, root_path, query=None):
        self._create_local_dir(root_path)
        children = self._list_children(folderId=root_id, query=query)

        for child in children:
            item = self._get_file(child['id'])
            path = os.path.join(root_path, item['title'])
            drive_item = GoogleDriveFile(self.service, path, item)
            self.drive_files[path] = drive_item

            if item['mimeType'] == folder_mime_type:
                self._synchronize_files(item['id'], path, query)
            if item.has_key('downloadUrl'):
                    drive_item.download_from_url()

    def _synchronize_files_by_type(self, root_path, query):
        self._create_local_dir(root_path)
        items = self._list_file(query=query)

        for item in items:
            path = os.path.join(root_path, item['title'])
            drive_item = GoogleDriveFile(self.service, path, item)
            self.drive_files[path] = drive_item

            if item['mimeType'] == folder_mime_type:
                self._synchronize_files(item['id'], path)
            if item.has_key('downloadUrl'):
                drive_item.download_from_url()

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

    def on_modified(self, path):
        if os.path.isdir(path):
            return
        print 'modified  %s' % path
        # self.drive_files[path].update(path)

    def on_create(self, path):
        print 'created   %s' % path

        sub_path = os.path.dirname(path)
        if not self.drive_files.has_key(sub_path):
            self.on_create(sub_path)

        # create drie item
        drive_file = GoogleDriveFile(self.service, path)
        drive_file.create(path, self.drive_files[sub_path].id)
        self.drive_files[path] = drive_file
        self._create_local_dir(path)

    def on_rename(self, src_path, dest_path):
        print 'rename from %s to %s' % (src_path, dest_path)
        parent = self._find_parent(dest_path)
        temp = self.drive_files[src_path]
        temp.update(dest_path, parent.id)
        del self.drive_files[src_path]
        self.drive_files[dest_path] = temp

    def _find_parent(self, path):
        if self.drive_files.has_key(path):
            return self.drive_files[path]
        head, _ = os.path.split(path)
        while not self.drive_files.has_key(head):
            head, _ = os.path.split(head)
        return self.drive_files[head]

    def _create_local_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
