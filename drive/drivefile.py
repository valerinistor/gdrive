from apiclient import errors
from apiclient.http import MediaFileUpload
import drive
import logging
import os

defaul_mime_type = 'application/octet-stream'
folder_mime_type = 'application/vnd.google-apps.folder'
partial_fields = 'id,title,downloadUrl,mimeType'
partial_item_fields = 'items(' + partial_fields + ')'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger_apiclient = logging.getLogger('apiclient.discovery')
logger_apiclient.setLevel(logging.WARNING)

class GoogleDriveFile:

    def __init__(self, path, metadata=None):
        self.path = path
        if metadata is not None:
            self.id = metadata['id']
            if metadata.has_key('downloadUrl'):
                self.download_url = metadata['downloadUrl']

    def _save_local_file(self, content):
        target = open(self.path, 'w')
        target.write(content)
        target.close()

    def get_file(self, file_id):
        try:
            return drive.service.files().get(
                     fileId=file_id,
                     fields=partial_fields).execute()
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)
        return None

    def download_from_url(self):
        if os.path.exists(self.path):
            return

        logger.info('downloading %s', self.path)

        resp, content = drive.service._http.request(self.download_url)
        if resp.status == 200:
            self._save_local_file(content)
        else:
            logger.error('an error occurred: %s', resp)

    def trash(self):
        try:
            logger.info('trashed %s', self.path)
            drive.service.files().trash(fileId=self.id).execute()
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)

    def untrash(self):
        try:
            logger.info('untrashed %s', self.path)
            drive.service.files().untrash(fileId=self.id).execute()
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)

    def delete(self):
        try:
            logger.info('deleted %s', self.path)
            drive.service.files().delete(fileId=self.id).execute()
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)

    def update(self, new_path=None, parent_id='root'):
        try:
            existing_file = self.get_file(self.id)

            if new_path is None:
                path = self.path
            else:
                path = new_path

            mime_type = defaul_mime_type
            media_body = None

            if not os.path.isdir(path):
                media_body = MediaFileUpload(path, resumable=True)
                if media_body.size() == 0:
                    logger.error('cannot update no content file %s', path)
                    return None
                if media_body.mimetype() is not None:
                    mime_type = media_body.mimetype()
                else:
                    media_body._mimetype = mime_type
            else:
                mime_type = folder_mime_type

            existing_file['title'] = os.path.basename(path)
            existing_file['parents'] = [{'id': parent_id}]
            existing_file['mimeType'] = mime_type

            logger.info('updated %s', path)
            return drive.service.files().update(
                fileId=self.id,
                body=existing_file,
                media_body=media_body).execute()
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
            metadata = drive.service.files().insert(
                body=body,
                media_body=media_body).execute()

            logger.info('created %s, %s', self.path, body['mimeType'])

            self.id = metadata['id']
            if metadata.has_key('downloadUrl'):
                self.download_url = metadata['downloadUrl']
            return metadata
        except errors.HttpError, error:
            logger.error('an error occurred: %s', error)
            return None
