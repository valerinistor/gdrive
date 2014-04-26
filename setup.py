from drive.filewatcher  import FileWatcher
from drive.drive import GoogleDrive
from oauth.oauth import GoogleOAuth

if __name__ == '__main__':

    # authenticate to Drive
    goauth = GoogleOAuth()
    goauth.authorize()
    drive = GoogleDrive(goauth.get_service())

    # synchronize files  Drive
    rootFolder = './GoogleDrive'
    drive.synchronize_files('root', rootFolder)
    drive.synchronize_shared_files(rootFolder)

    # start watching files for changes
    watcher = FileWatcher(rootFolder)
    watcher.start()
    try:
        while watcher.is_alive():
            watcher.join(1)
    except (KeyboardInterrupt, SystemExit):
        print 'Shutting down ...'
        watcher.request_stop()
