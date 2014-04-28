from apiclient import errors
import os

class GoogleDriveFile:

    def __init__(self, service, path, metadata):
        self.service = service
        self.id = metadata['id']
        self.download_url = metadata['downloadUrl']
        self.path = path

    def _save_local_file(self, content):
        target = open(self.path, 'w')
        target.write(content)
        target.close()

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
        pass

    def create(self):
        pass