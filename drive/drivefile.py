from apiclient import errors
from apiclient.http import MediaFileUpload
import drive
import logging
import os

defaul_mime_type = 'application/octet-stream'
folder_mime_type = 'application/vnd.google-apps.folder'
partial_fields = 'id,title,downloadUrl,mimeType,parents,md5Checksum'
partial_item_fields = 'items(' + partial_fields + ')'

FORMAT = "%(levelname)-7s [%(asctime)s] [PID:%(process)d] [%(threadName)-10s] [%(name)-20s] [%(filename)-15s:%(lineno)-3d] : %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger(__name__)
logging.getLogger('apiclient.discovery').setLevel(logging.WARNING)

class GoogleDriveFile:

    def __init__(self, path, metadata=None):
        self.path = path
        if metadata is not None:
            self.id = metadata['id']
            if metadata.has_key('downloadUrl'):
                self.download_url = metadata['downloadUrl']
            if metadata.has_key('md5Checksum'):
                self.md5Checksum = metadata['md5Checksum']

    def _save_local_file(self, content):
        head, _ = os.path.split(self.path)
        if not os.path.exists(head):
            os.makedirs(head)

        target = open(self.path, 'w')
        target.write(content)
        target.close()

    def get_file(self, file_id):
        try:
            if not hasattr(self, 'id'):
                logger.error('cannot retrieve %s item is not on drive',
                             self.path)
                return

            return drive.service.files().get(
                     fileId=file_id,
                     fields=partial_fields).execute()
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)
        return None

    def download_from_url(self):
        logger.info('downloading %s', self.path)

        resp, content = drive.service._http.request(self.download_url)
        if resp.status == 200:
            self._save_local_file(content)
        else:
            logger.error('an error occurred: %s', resp)

    def trash(self):
        try:
            if not hasattr(self, 'id'):
                logger.error('cannot trash %s item is not on drive',
                             self.path)
                return

            logger.info('trashed %s', self.path)
            drive.service.files().trash(fileId=self.id).execute()
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)

    def untrash(self):
        try:
            if not hasattr(self, 'id'):
                logger.error('cannot untrash %s item is not on drive',
                             self.path)
                return

            logger.info('untrashed %s', self.path)
            drive.service.files().untrash(fileId=self.id).execute()
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)

    def delete(self):
        try:
            if not hasattr(self, 'id'):
                logger.error('cannot delete %s item is not on drive',
                             self.path)
                return

            logger.info('deleted %s', self.path)
            with drive.lock:
                drive.service.files().delete(fileId=self.id).execute()
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)

    def update(self, new_path=None, parent_id='root'):
        try:
            if not hasattr(self, 'id'):
                return self.create(parent_id)

            existing_file = self.get_file(self.id)

            if new_path is not None:
                self.path = new_path

            mime_type = defaul_mime_type
            media_body = None

            if not os.path.isdir(self.path):
                media_body = MediaFileUpload(self.path, resumable=True)
                if media_body.size() == 0:
                    logger.error('cannot update no content file %s', self.path)
                    return None
                if media_body.mimetype() is not None:
                    mime_type = media_body.mimetype()
                else:
                    media_body._mimetype = mime_type
            else:
                mime_type = folder_mime_type

            existing_file['title'] = os.path.basename(self.path)
            existing_file['parents'] = [{'id': parent_id}]
            existing_file['mimeType'] = mime_type

            logger.info('updated %s', self.path)
            with drive.lock:
                metadata = drive.service.files().update(
                    fileId=self.id,
                    body=existing_file,
                    media_body=media_body).execute()

            self.id = metadata['id']
            if metadata.has_key('downloadUrl'):
                self.download_url = metadata['downloadUrl']
            if metadata.has_key('md5Checksum'):
                self.md5Checksum = metadata['md5Checksum']
            return metadata
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)
            return None

    def create(self, parent_id='root'):
        mime_type = defaul_mime_type
        media_body = None

        if not os.path.isdir(self.path):
            media_body = MediaFileUpload(self.path, resumable=True)
            if media_body.size() == 0:
                logger.error('cannot create no content file %s', self.path)
                return None
            if media_body.mimetype() is not None:
                mime_type = media_body.mimetype()
            else:
                media_body._mimetype = mime_type
        else:
            mime_type = folder_mime_type

        body = {
            'title': os.path.basename(self.path),
            'mimeType': mime_type,
            'parents': [{'id': parent_id}]
        }

        try:
            with drive.lock:
                metadata = drive.service.files().insert(
                    body=body,
                    media_body=media_body).execute()

            logger.info('created %s, %s', self.path, body['mimeType'])

            self.id = metadata['id']
            if metadata.has_key('downloadUrl'):
                self.download_url = metadata['downloadUrl']
            if metadata.has_key('md5Checksum'):
                self.md5Checksum = metadata['md5Checksum']
            return metadata
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)
            return None
