from apiclient import errors
from drivefile import GoogleDriveFile
from drivefile import folder_mime_type
from filewatcher  import FileWatcher
from service import Service
import logging
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleDrive:

    def __init__(self, root_folder):
        self.root_folder = root_folder
        self.drive_files = {}
        root_metadata = {'id': 'root'}
        root_item = GoogleDriveFile(root_folder, root_metadata)
        self.drive_files[root_folder] = root_item

    def synchronize_drive(self):
        shared_folder = os.path.join(self.root_folder, 'SharedWithMe')
        trash_folder = os.path.join(self.root_folder, 'Trash')

        # synchronize drive files
        self._synchronize_files('root', self.root_folder, query='not trashed')
        # synchronize shared files
        # self._synchronize_files_by_type(shared_folder, 'sharedWithMe')
        # synchronize trashed files
        # self._synchronize_files_by_type(
        #    trash_folder,
        #    "trashed and 'root' in parents")

        # start watching files for changes
        watcher = FileWatcher(self, self.root_folder)
        watcher.start()

        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            watcher.stop()
        watcher.join()

    def _synchronize_files(self, root_id, root_path, query=None):
        self._create_local_dir(root_path)
        children = self._list_children(folderId=root_id, query=query)

        for child in children:
            item = self._get_file(child['id'])
            path = os.path.join(root_path, item['title'])
            drive_item = GoogleDriveFile(path, item)
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
            drive_item = GoogleDriveFile(path, item)
            self.drive_files[path] = drive_item

            if item['mimeType'] == folder_mime_type:
                self._synchronize_files(item['id'], path)
            if item.has_key('downloadUrl'):
                drive_item.download_from_url()

    def _list_file(self, query=None):
        items = []
        try:
            items = Service.service.files().list(q=query).execute()['items']
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)
        return items

    def _list_children(self, folderId, query=None):
        items = []
        try:
            items = Service.service.children().list(
                q=query,
                folderId=folderId).execute()['items']
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)
        return items

    def _get_file(self, file_id):
        try:
            return Service.service.files().get(fileId=file_id).execute()
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)
            return None

    def on_delete(self, path):
        to_delete = self.drive_files[path]
        to_delete.delete()
        del self.drive_files[path]

    def on_modified(self, path):
        if os.path.isdir(path):
            return
        self.drive_files[path].update(path)

    def on_create(self, path):
        head, _ = os.path.split(path)
        if not self.drive_files.has_key(head):
            self.on_create(head)

        # create drive item
        parent = self._find_parent(head)
        to_create = GoogleDriveFile(path)
        to_create.create(parent.id)
        self.drive_files[path] = to_create

    def on_rename(self, src_path, dest_path):
        logger.info('renamed from %s to %s', src_path, dest_path)

        parent = self._find_parent(dest_path)
        temp = self.drive_files[src_path]
        temp.update(dest_path, parent.id)
        self.drive_files[dest_path] = temp
        del self.drive_files[src_path]

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
