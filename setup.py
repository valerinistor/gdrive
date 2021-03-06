#! /usr/bin/python2.7

from drive.drive import GoogleDrive
from oauth.oauth import GoogleOAuth
import os

if __name__ == '__main__':

    # authenticate to Drive
    root_folder = os.environ['HOME'] + '/GoogleDrive'
    goauth = GoogleOAuth()
    goauth.authorize()

    gdrive = GoogleDrive(goauth.get_service(), root_folder)

    # synchronize files  Drive
    gdrive.synchronize_drive()
