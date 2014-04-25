from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from apiclient import errors
from oauth2client.file import Storage
import argparse
import httplib2
import os

# Parser for command-line arguments.
parser = argparse.ArgumentParser( 
    description = __doc__,
    formatter_class = argparse.RawDescriptionHelpFormatter,
    parents = [tools.argparser] )

client_secret = os.path.join( os.path.dirname( __file__ ), 'client_secrets.json' )

scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.appdata',
    'https://www.googleapis.com/auth/drive.apps.readonly',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.scripts'
  ]

flow = client.flow_from_clientsecrets( client_secret, scope, message = tools.message_if_missing( client_secret ) )


class GoogleOAuth:
    def __init__( self ):
        pass

    def authorize( self ):
        argv = ['--logging_level DEBUG']
        flags = parser.parse_args( argv[1:] )

        storage = Storage( os.path.join( os.path.dirname( __file__ ), 'credentials' ) )

        credentials = storage.get()
        http = httplib2.Http()

        if credentials is None or credentials.invalid:
            credentials = tools.run_flow( flow, storage, flags, http = http )

        http = credentials.authorize( http )

        # Construct the service object for the interacting with the Drive API.
        return discovery.build( 'drive', 'v2', http = http )

    def downoadFiles( self, service ):
        try:
            page_token = None
            while True:
                try:
                    param = {}
                    if page_token:
                        param['pageToken'] = page_token
                    files = service.files().list(**param).execute()
                    items = files['items']

                    for fileitem in items:
                        if fileitem.has_key('downloadUrl'):
                            download_url = fileitem['downloadUrl']
                            filename = fileitem['title']
                            print 'Downloading %s' % filename

                            resp, content = service._http.request(download_url)
                            if resp.status == 200:
                                target = open (filename, 'w')
                                target.write(content)
                                target.close()
                            else:
                                print 'An error occurred: %s' % resp
                    page_token = files.get('nextPageToken')
                    if not page_token:
                        break
                except errors.HttpError, error:
                    print 'An error occurred: %s' % error
                    break
        except client.AccessTokenRefreshError:
            print ( "The credentials have been revoked or expired, please re-run"
                    "the application to re-authorize" )

    def downoadFilesWithFolders(self, service, root_id, root_path):

        if not os.path.exists(root_path):
            os.makedirs(root_path)

        children = service.children().list(folderId=root_id).execute()['items']

        for child in children:
            item = service.files().get(fileId=child['id']).execute()
            path = os.path.join( root_path, item['title'] )
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                self.downoadFilesWithFolders(service, item['id'], path)
            else:
                if item.has_key('downloadUrl'):
                    download_url = item['downloadUrl']
                    print 'Downloading %s' % path
                    resp, content = service._http.request(download_url)
                    if resp.status == 200:
                        target = open (path, 'w')
                        target.write(content)
                        target.close()
                    else:
                        print 'An error occurred: %s' % resp
