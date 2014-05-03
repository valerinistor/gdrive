#! /usr/bin/python2.7

from drive.drive import GoogleDrive
from drive.service import Service
from oauth.oauth import GoogleOAuth

if __name__ == '__main__':

    # authenticate to Drive
    root_folder = './GoogleDrive'
    goauth = GoogleOAuth()
    goauth.authorize()
    service = Service()
    service.service = goauth.get_service()
    drive = GoogleDrive(root_folder)

    # synchronize files  Drive
    drive.synchronize_drive()
