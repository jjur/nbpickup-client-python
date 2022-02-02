import requests
import os
import re
import asyncio
import logging

from watchdog.observers import Observer
from nbpickup.EventHandlers.autosave_authoring import AutoSaveEventHandler
from nbpickup.EventHandlers.autosave_gradebook import GradebookAutoSaveEventHandler
from watchdog.events import FileSystemEventHandler

from nbpickup.gradebook_tools import get_gradebook_content_stats
# Setting up the logging
logger = logging.getLogger(__name__)

log_file = logging.FileHandler("nbpickup.log")
log_console = logging.StreamHandler()

log_file.setLevel(logging.DEBUG)
log_console.setLevel(logging.WARNING)

log_file.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
log_console.setFormatter(logging.Formatter('%(name)s - %(levelname)s - %(message)s'))

logger.addHandler(log_file)
logger.addHandler(log_console)
logger.setLevel(logging.DEBUG)


def get_path_and_filename(full_path):
    path = "/".join(full_path.split("/")[:-1])
    filename = full_path.split("/")[-1]
    return path, filename


class Authoring():
    """
    Class for handling the process of creating files and establishing the autosaving process
    """

    def __init__(self, server_url):
        self.server_url = server_url
        # To be assigned when authentication is done
        self.source_folder = None
        self.release_folder = None
        self.alias = None
        self.token = None
        self.file_records = {}
        self.assignment = None
        self.headers = {}
        logger.info("Authoring nbpickup.authoring initialized.")

    def auth(self, access_token):

        headers = {'Authorization': f'Bearer {access_token}'}

        response = requests.get(self.server_url + "/API/auth", headers=headers)

        if response.status_code == 200:
            self.headers = headers
            self.token = access_token
            self.assignment = response.json()
            self.alias = self.assignment["a_alias"]

            self.source_folder = os.getcwd() + "/source/" + self.alias
            self.release_folder = os.getcwd() + "/release/"

            # Create these folders if does not exit:
            if not os.path.exists(self.source_folder):
                os.makedirs(self.source_folder)
            if not os.path.exists(self.release_folder):
                os.makedirs(self.release_folder)

            print("Assignment Loaded:", self.assignment["a_name"])
        else:
            logger.error("AUTH|Server responded with code " + str(response.status_code) + ": " + str(response.content))
            print(response.content)
            raise Exception(response.content)

    def get_files(self):
        response = requests.get(self.server_url + "/API/list_files", headers=self.headers)

        if response.status_code == 200:
            files = response.json()
            for file in files:
                if file["private"]:
                    folder = self.source_folder
                else:
                    folder = self.release_folder

                self.download_file(file["file"], folder)
        else:
            logger.error(
                "GET_FILES|Server responded with code " + str(response.status_code) + ": " + str(response.content))
            print(response.content)
            raise Exception(response.content)

    def download_file(self, file_id, location, filename=False):

        # Make sure that the folder is available
        if not os.path.exists(location):
            os.makedirs(location)

        response = requests.get(self.server_url + "/API/get_file/" + str(file_id), headers=self.headers)

        if response.status_code == 200:
            if not filename:
                # Find the filename from the headers
                d = response.headers['content-disposition']
                filename = re.findall("filename=(.+)", d)[0]

            open(location + "/" + filename, 'wb').write(response.content)
            self.file_records[location + "/" + filename] = file_id
        else:
            print(response.content)
            # raise Exception(response.content)

    def autosave(self):
        global observer

        event_handler_source = AutoSaveEventHandler(self, self.source_folder, private=1)
        event_handler_release = AutoSaveEventHandler(self, self.release_folder, private=0)
        event_handler_gradebook = GradebookAutoSaveEventHandler(self)
        observer = Observer()

        observer.schedule(event_handler_source, self.source_folder, recursive=True)
        observer.schedule(event_handler_release, self.release_folder, recursive=True)
        observer.schedule(event_handler_gradebook, os.path.join(os.getcwd(), "gradebook.db"))
        observer.start()

        loop = asyncio.get_event_loop()
        loop.create_task(self.async_autosaving())

    async def async_autosaving(self):
        global observer
        await asyncio.sleep(1)
        minutes = 0
        while True:
            await asyncio.sleep(60);
            minutes += 1
            if minutes % 10 == 0:
                print(" ", sep="", end="")

    def show_links(self):
        try:
            from IPython.display import display, Javascript, HTML, IFrame
        except ImportError:
            logger.error("Unable to load IPYthon library.")
            return False

        display(HTML(f"""<a id="btn_source_folder" target="_blank" href="../tree/source/{self.alias}" class="btn btn-primary">Open Assignment Folder</a>
        <a id="btn_release_folder" target="_blank" href="../tree/release/{self.alias}" class="btn btn-primary">Open Student´s version Folder</a>
        <a id="btn_nbgrader" target="_blank" href="../formgrader" class="btn btn-primary">Open nbgrader</a>"""))

    def upload_file(self, file, directory, private=1, additional_data=None):
        """Uploads new file to the nbpickup server"""
        # Skip files starting the name with dot
        if file[0] == "." or "checkpoint" in file:
            return False
        files = {"file": open(directory + "/" + file, "rb")}
        values = {"filename": file,
                  "path": directory,
                  "assignment": self.assignment["a_id"],
                  "private": private,
                  "filetype": "file"}

        if additional_data:
            for key in additional_data:
                values[key] = additional_data[key]
        response = requests.post(self.server_url + "/API/upload_file", files=files, data=values, headers=self.headers)
        if response.status_code == 200:
            file_id = int(response.text)
            self.file_records[directory + "/" + file] = file_id

        else:
            logger.error(
                "UPLOAD_FILE|Server responded with code " + str(response.status_code) + ": " + str(response.content))

    def update_file(self, file, directory, additional_data=None):
        """Updates existing file on the nbpickup server"""
        # Skip files starting the name with dot
        if file[0] == "." or "checkpoint" in file:
            return False
        files = {"file": open(directory + "/" + file, "rb")}
        values = {"filename": file,
                  "path": directory,
                  "filetype": "file"}

        if additional_data:
            for key in additional_data:
                values[key] = additional_data[key]

        # Check if the file is already in our know directory
        if directory + "/" + file not in self.file_records:
            return self.upload_file(file, directory)

        file_id = self.file_records[directory + "/" + file]
        response = requests.post(self.server_url + f"/API/update_file/{file_id}", files=files, data=values,
                                 headers=self.headers)
        if response.status_code == 200:
            logger.info("UPDATE_FILE| File autosaved" + str(file) + ": ")  # Nice, updated
            pass  # Nice, updated

        else:
            logger.error(
                "UPDATE_FILE|Server responded with code " + str(response.status_code) + ": " + str(response.content))

    def move_file(self, old_location, new_location):
        """Function to handle file movements. Mainly for bookkeeping purposes."""
        directory, filename = get_path_and_filename(new_location)
        if old_location not in self.file_records:
            return self.upload_file(filename, directory)
        else:
            self.file_records[new_location] = self.file_records[old_location]
            return self.update_file(filename, directory)


    def update_gradebook_file(self, filename, path):
        """Performs preprocessing of gradebook file and then uploads Gradebook as file"""
        num_assignments, num_students = get_gradebook_content_stats(filename, path)

        metrics = {"stats_students": num_students,
                   "stats_assignments": num_assignments,
                   "filetype":"gradebook"}

        return self.upload_file(filename,path, additional_data=metrics)


    def upload_gradebook_file(self, filename, path):
        """Performs preprocessing of gradebook file and then uploads Gradebook as file"""
        num_assignments, num_students = get_gradebook_content_stats(filename, path)

        metrics = {"stats_students": num_students,
                   "stats_assignments": num_assignments,
                   "filetype": "gradebook"}

        return self.upload_file(filename, path, additional_data=metrics)

