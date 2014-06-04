from apiclient import errors
from drivefile import GoogleDriveFile
from drivefile import folder_mime_type
from drivefile import partial_fields
from drivefile import partial_item_fields
from filewatcher  import FileWatcher
from drivechanges import DriveChanges
import drive
import logging
import os
import time
import shutil
import threading

service = {}
lock = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleDrive:

    def __init__(self, srv, root_folder):
        drive.drive.service = srv
        drive.drive.lock = threading.Lock()

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
        self._synchronize_files_by_type(
           trash_folder,
           "trashed and 'root' in parents")

        # start watching files for changes
        local_watcher = FileWatcher(self, self.root_folder)
        local_watcher.start()

        drive_watcher = DriveChanges(self)
        drive_watcher.start()

        try:
            while True:
                time.sleep(1)
        except (KeyboardInterrupt, SystemExit):
            local_watcher.stop()
            drive_watcher.stop()
        local_watcher.join()
        drive_watcher.join()

    def _synchronize_files(self, root_id, root_path, query=None):
        self._create_local_dir(root_path)
        children = self._list_children(folderId=root_id, query=query)

        for child in children:
            item = self._get_remote_file(child['id'])
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
            items = service.files().list(
                     q=query,
                     fields=partial_item_fields).execute()['items']
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)
        return items

    def _list_children(self, folderId, query=None):
        items = []
        try:
            items = service.children().list(
                q=query,
                folderId=folderId).execute()['items']
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)
        return items

    def _get_remote_file(self, file_id):
        try:
            return service.files().get(
                       fileId=file_id,
                       fields=partial_fields).execute()
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)
            return None

    def on_local_delete(self, path):
        if not self.drive_files.has_key(path):
            return

        to_delete = self.drive_files[path]
        to_delete.delete()
        del self.drive_files[path]

    def on_local_modified(self, path):
        if not self.drive_files.has_key(path):
            return

        if os.path.isdir(path):
            return
        self.drive_files[path].update(path)

    def on_local_create(self, path):
        head, _ = os.path.split(path)
        if not self.drive_files.has_key(head):
            self.on_local_create(head)

        if  self.drive_files.has_key(path):
            logger.info('file %s already exists', path)
            return

        # create drive item
        parent = self._find_parent(head)
        to_create = GoogleDriveFile(path)
        to_create.create(parent.id)
        self.drive_files[path] = to_create

    def on_local_rename(self, src_path, dest_path):
        if not self.drive_files.has_key(src_path):
            return

        logger.info('renamed from %s to %s', src_path, dest_path)

        parent = self._find_parent(dest_path)
        temp = self.drive_files[src_path]
        temp.update(dest_path, parent.id)
        self.drive_files[dest_path] = temp
        del self.drive_files[src_path]

    def notify_drive_changes(self, changes):
        for change in changes:
            local_file = self._get_local_file(change['fileId'])
            # file does not exists locally
            if local_file is None:
                if not change['deleted']:
                    self.on_drive_create(change)
            # file exists locally
            else:
                if change['deleted']:
                    self.on_drive_delete(local_file.path)
                else:
                    if change.has_key('file'):
                        if os.path.basename(local_file.path) != change['file']['title']:
                            self.on_drive_rename(local_file, change['file'])
                        else:
                            self.on_drive_modified(local_file, change['file'])

    def on_drive_delete(self, path):
        if not self.drive_files.has_key(path):
            return

        logger.info('drive change: delete %s', path)

        if os.path.isfile(path):
            os.remove(path)
        else:
            shutil.rmtree(path)
        del self.drive_files[path]

    def on_drive_modified(self, local_file, file_metadata):
        if os.path.isdir(local_file.path) or file_metadata['mimeType'] == folder_mime_type:
            return

        if not local_file.md5Checksum == file_metadata['md5Checksum']:
            logger.info('drive change: modified %s', file_metadata['title'])
            local_file.download_from_url()
            local_file.md5Checksum = file_metadata['md5Checksum']
        else:
            logger.info('drive change: unknown change for %s', local_file.path)

    def on_drive_create(self, change_metadata):
        # TODO refactor this method
        remote_file = self._get_remote_file(change_metadata['fileId'])
        path = ''
        while not remote_file['parents'][0]['isRoot']:
            path = os.path.join(remote_file['title'], path)
            remote_file = self._get_remote_file(remote_file['parents'][0]['id'])
        path = os.path.join(remote_file['title'], path)
        remote_file = self._get_remote_file(remote_file['parents'][0]['id'])
        path = os.path.join(self.root_folder, path)[0:-1]

        remote_file = self._get_remote_file(change_metadata['fileId'])
        drive_item = GoogleDriveFile(path, remote_file)
        self.drive_files[path] = drive_item

        if remote_file['mimeType'] == folder_mime_type:
            self._create_local_dir(path)
        if remote_file.has_key('downloadUrl'):
            drive_item.download_from_url()

    def on_drive_rename(self, local_file, file_metadata):
        new_path = os.path.join(os.path.dirname(local_file.path), file_metadata['title'])
        to_create = GoogleDriveFile(new_path, file_metadata)

        self.drive_files[new_path] = to_create
        del self.drive_files[local_file.path]

        logger.info('drive change: renamed from %s to %s', local_file.path, new_path)
        os.rename(local_file.path, new_path)

    def _get_local_file(self, file_id):
        for key in self.drive_files:
            if self.drive_files[key].id == file_id:
                return self.drive_files[key]
        return None

    def _find_parent(self, path):
        if self.drive_files.has_key(path):
            return self.drive_files[path]
        head, _ = os.path.split(path)
        while not self.drive_files.has_key(head):
            head, _ = os.path.split(head)
        return self.drive_files[head]

    def _create_local_dir(self, path):
        if not os.path.exists(path):
            logger.info("creating directory %s", path)
            os.makedirs(path)
