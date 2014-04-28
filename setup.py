#! /usr/bin/python2.7

from drive.drive import GoogleDrive
from drive.filewatcher  import FileWatcher
from oauth.oauth import GoogleOAuth


if __name__ == '__main__':

    # authenticate to Drive
    root_folder = './GoogleDrive'
    goauth = GoogleOAuth()
    goauth.authorize()
    drive = GoogleDrive(root_folder, goauth.get_service())

    # synchronize files  Drive
    drive.synchronize_drive()

    # start watching files for changes
    watcher = FileWatcher(drive, root_folder)
    watcher.start()

    try:
        while watcher.is_alive():
            watcher.join(1)
    except (KeyboardInterrupt, SystemExit):
        print 'Shutting down ...'
        watcher.request_stop()
