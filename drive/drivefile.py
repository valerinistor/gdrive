from apiclient import errors
from apiclient.http import MediaFileUpload
import os

class GoogleDriveFile:

    def __init__(self, service, path, metadata=None):
        self.service = service
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
            return self.service.files().get(fileId=file_id).execute()
        except errors.HttpError, error:
            print 'An error occurred: %s' % error

    def download_from_url(self):
        if os.path.exists(self.path):
            return
        print 'Downloading %s' % self.path
        resp, content = self.service._http.request(self.download_url)
        if resp.status == 200:
            self._save_local_file(content)
        else:
            print 'An error occurred: %s' % resp

    def trash(self):
        try:
            self.service.files().trash(fileId=self.id).execute()
        except errors.HttpError, error:
            print 'An error occurred: %s' % error

    def delete(self):
        try:
            self.service.files().delete(fileId=self.self.id).execute()
        except errors.HttpError, error:
            print 'An error occurred: %s' % error

    def update(self):
        try:
            existing_file = self.get_file(self.id)
            existing_file['title'] = os.path.basename(self.path)

            media_body = MediaFileUpload(self.path, resumable=True)

            return self.service.files().update(
                fileId=self.id,
                body=existing_file,
                media_body=media_body).execute()
        except errors.HttpError, error:
            print 'An error occurred: %s' % error
            return None

    def create(self, path, parent_id='root'):
        self.path = path
        media_body = MediaFileUpload(path, resumable=True)

        body = {
            'title': os.path.basename(path),
            'parents': [{'id': parent_id}]
        }

        try:
            metadata = self.service.files().insert(
                body=body,
                media_body=media_body).execute()

            self.id = metadata['id']
            if metadata.has_key('downloadUrl'):
                self.download_url = metadata['downloadUrl']

            return metadata
        except errors.HttpError, error:
            print 'An error occured: %s' % error
            return None
