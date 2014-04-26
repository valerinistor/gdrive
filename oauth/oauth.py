from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import argparse
import httplib2
import os

# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[tools.argparser])

client_secret = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.appdata',
    'https://www.googleapis.com/auth/drive.apps.readonly',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata.readonly',
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/drive.scripts'
  ]

flow = client.flow_from_clientsecrets(client_secret, scope, message=tools.message_if_missing(client_secret))


class GoogleOAuth:
    def __init__(self):
        self.service = dict()

    def authorize(self):
        argv = ['--logging_level DEBUG']
        flags = parser.parse_args(argv[1:])

        storage = Storage(os.path.join(os.path.dirname(__file__), 'credentials.json'))

        credentials = storage.get()
        http = httplib2.Http()

        if credentials is None or credentials.invalid:
            credentials = tools.run_flow(flow, storage, flags, http=http)

        http = credentials.authorize(http)

        # Construct the service object for the interacting with the Drive API.
        self.service = discovery.build('drive', 'v2', http=http)

    def get_service(self):
        return self.service
