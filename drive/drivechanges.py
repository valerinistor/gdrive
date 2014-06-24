from apiclient import errors
import drive
import logging
import threading
import time
import sys
import traceback
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DriveChanges (threading.Thread):

    def __init__(self, drive):
        threading.Thread.__init__(self)
        self.drive = drive
        self._stop_requested = False

    def run(self):
        self._watch_for_drive_changes()

    def stop(self):
        self._stop_requested = True

    def _watch_for_drive_changes(self):
        logger.info('start watching for drive changes')

        changes, largestChangeId = self._retrieve_all_changes()
        while not self._stop_requested:
            try:
                time.sleep(15)
                changes, largestChangeId = self._retrieve_all_changes(largestChangeId + 1)

                if len(changes) == 0:
                    continue

                self.drive.notify_drive_changes(changes)
            except:
                _, exc_value, exc_tb = sys.exc_info()
                filename, line_nr, func_name, _ = traceback.extract_tb(exc_tb)[-1]
                err_details = '%s:%s:%s' % (os.path.basename(filename), func_name, line_nr)
                logger.error('An error occurred in %s, at %s: %s', self.name, err_details, exc_value.message)

    def _retrieve_all_changes(self, start_change_id=None):
        result = []
        page_token = None
        largestChangeId = 0
        while True:
            try:
                param = {}
                if start_change_id:
                    param['startChangeId'] = start_change_id
                if page_token:
                    param['pageToken'] = page_token
                with drive.lock:
                    changes = drive.service.changes().list(**param).execute()

                result.extend(changes['items'])
                largestChangeId = int(changes['largestChangeId'])
                page_token = changes.get('nextPageToken')
                if not page_token:
                    break
            except errors.HttpError, error:
                logger.error('An error occurred: %s', error)
                break
        return (result, largestChangeId)
