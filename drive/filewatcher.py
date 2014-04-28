import os
import threading
import time

class FileWatcher (threading.Thread):

    def __init__(self, drive, path_to_watch):
        threading.Thread.__init__(self)
        self.path_to_watch = path_to_watch
        self.drive = drive
        self._stop_requested = False

    def run(self):
        self._watch_files(self.path_to_watch)

    def request_stop(self):
        self._stop_requested = True

    def _files_to_timestamp(self, path):
        result = {}
        for root, _, files in os.walk(path):
            for file_to_watch in files:
                f = os.path.join(root, file_to_watch)
                result[f] = os.path.getmtime(f)
        return result

    def _watch_files(self, path_to_watch):
        print "watching ", path_to_watch
        before = self._files_to_timestamp(path_to_watch)

        while not self._stop_requested:
            time.sleep(2)
            after = self._files_to_timestamp(path_to_watch)

            added = [f for f in after.keys() if not f in before.keys()]
            removed = [f for f in before.keys() if not f in after.keys()]
            modified = []

            for f in before.keys():
                if not f in removed:
                    if os.path.getmtime(f) != before.get(f):
                        modified.append(f)

            map(self.drive.on_create, added)
            map(self.drive.on_delete, removed)
            map(self.drive.on_modified, modified)

            before = after
