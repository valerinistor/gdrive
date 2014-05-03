#! /usr/bin/python2.7

from drive.drive import GoogleDrive
from oauth.oauth import GoogleOAuth

if __name__ == '__main__':

    # authenticate to Drive
    root_folder = './GoogleDrive'
    goauth = GoogleOAuth()
    goauth.authorize()
    drive = GoogleDrive(root_folder, goauth.get_service())

    # synchronize files  Drive
    drive.synchronize_drive()
