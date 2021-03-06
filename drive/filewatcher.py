import logging
import os
import threading
import time
import sys
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileWatcher (threading.Thread):

    def __init__(self, drive, path_to_watch):
        threading.Thread.__init__(self)
        self.path_to_watch = path_to_watch
        self.drive = drive
        self._stop_requested = False

    def run(self):
        self._watch_files()

    def stop(self):
        self._stop_requested = True

    def _files_to_timestamp(self, path):
        result = {}
        for root, dirs, files in os.walk(path):
            files += dirs
            for file_to_watch in files:
                if file_to_watch.startswith('.'):
                    continue
                f = os.path.join(root, file_to_watch)
                fstat = os.stat(f)
                result[fstat.st_ino] = {'mtime': os.path.getmtime(f), 'path': f}
        return result

    def _watch_files(self):
        logger.info('start watching %s', self.path_to_watch)

        before = self._files_to_timestamp(self.path_to_watch)

        while not self._stop_requested:
            try:
                time.sleep(3)
                after = self._files_to_timestamp(self.path_to_watch)
                # added = [f for f in after.keys() if not f in before.keys()]
                removed = [f for f in before.keys() if not f in after.keys()]

#                for b in before.keys():
#                    for a in after.keys():
#                        if after[a]['path'] == before[b]['path'] and a != b:
#                            temp = after[a]
#                            del after[a]
#                            after[b] = temp

                for f in before.keys():
                    # remove
                    if not f in after.keys():
                        self.drive.on_local_delete(before[f]['path'])
                        continue
                    # rename
                    if after[f]['path'] != before[f]['path']:
                        self.drive.on_local_rename(before[f]['path'], after[f]['path'])
                        continue

                    # modified
                    if not f in removed:
                        if os.path.getmtime(before[f]['path']) != before[f]['mtime']:
                            self.drive.on_local_modified(before[f]['path'])

                # added
                for f in after.keys():
                    if not f in before.keys():
                        self.drive.on_local_create(after[f]['path'])

                before = after
            except:
                _, exc_value, exc_tb = sys.exc_info()
                filename, line_nr, func_name, _ = traceback.extract_tb(exc_tb)[-1]
                err_details = '%s:%s:%s' % (os.path.basename(filename), func_name, line_nr)
                logger.error('An error occurred in %s, at %s: %s', self.name, err_details, exc_value.message)
