from apiclient import errors
import os

class GoogleDrive:

    def __init__(self, service):
        self.service = service

    def synchronize_files(self, root_id, root_path):
        self._create_local_dir(root_path)
        children = self._list_children(folderId=root_id)

        for child in children:
            item = self._get_file(child['id'])
            path = os.path.join(root_path, item['title'])
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                self.synchronize_files(item['id'], path)
            else:
                if item.has_key('downloadUrl'):
                    print 'Downloading %s' % path
                    self._save_local_file(self._download_from_url(item['downloadUrl']), path)

    def synchronize_shared_files(self, root_path):
        root_path = os.path.join(root_path, 'SharedWithMe')
        self._create_local_dir(root_path)
        items = self._list_file()

        for item in items:
            if item['shared']:
                if item.has_key('downloadUrl'):
                    path = os.path.join(root_path, item['title'])
                    print 'Downloading %s' % path
                    self._save_local_file(self._download_from_url(item['downloadUrl']), path)

    def _list_file(self, query=None):
        result = []
        page_token = None
        while True:
            try:
                param = {}
                param['q'] = query
                if page_token:
                    param['pageToken'] = page_token
                files = self.service.files().list(**param).execute()

                result.extend(files['items'])
                page_token = files.get('nextPageToken')
                if not page_token:
                    break
            except errors.HttpError, error:
                print 'An error occurred: %s' % error
                break
        return result

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

    def _download_from_url(self, url):
        resp, content = self.service._http.request(url)
        if resp.status == 200:
            return content
        else:
            print 'An error occurred: %s' % resp

    def _save_local_file(self, content, path):
        target = open(path, 'w')
        target.write(content)
        target.close()

    def _create_local_dir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)
