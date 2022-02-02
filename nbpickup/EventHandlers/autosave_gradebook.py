import logging
from watchdog.events import FileSystemEventHandler

# Setting up the logging
logger = logging.getLogger(__name__)

log_file = logging.FileHandler("nbpickup_autosaving.log")
log_console = logging.StreamHandler()

log_file.setLevel(logging.DEBUG)
log_console.setLevel(logging.WARNING)

log_file.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
log_console.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))

logger.addHandler(log_file)
logger.addHandler(log_console)
logger.setLevel(logging.DEBUG)

class GradebookAutoSaveEventHandler(FileSystemEventHandler):
    """Captures and deals with autosaving of nbpickup files"""

    def __init__(self, nbpickup_client, folder = "/"):
        super().__init__()

        self.nbpickup = nbpickup_client
        self.folder = folder

    def on_moved(self, event):
        """Handles both rename and move events"""
        super().on_moved(event)
        logger.warning("Gradebook Moved: from %s to %s" % (event.src_path, event.dest_path))

    def on_created(self, event):
        super().on_created(event)

        what = 'directory' if event.is_directory else 'file'

        logger.info("Created %s: %s" % (what, event.src_path))
        if not event.is_directory:
            path = "/".join(event.src_path.split("/")[:-1])
            filename = event.src_path.split("/")[-1]
            self.nbpickup.upload_gradebook_file(filename, path)

    def on_deleted(self, event):
        super().on_deleted(event)
        logger.warning("Gradebook Deleted: %s" % (event.src_path))

    def on_modified(self, event):
        super().on_modified(event)

        what = 'directory' if event.is_directory else 'file'
        logger.info("Modified %s: %s" % (what, event.src_path))
        if not event.is_directory:
            path = "/".join(event.src_path.split("/")[:-1])
            filename = event.src_path.split("/")[-1]
            self.nbpickup.update_gradebook_file(filename, path)
