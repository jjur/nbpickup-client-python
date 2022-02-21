import logging
import os
import requests
import json
import re

import asyncio
import logging

from watchdog.observers import Observer
from nbpickup.EventHandlers.autosave_gradebook import GradebookAutoSaveEventHandler

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


class Grading():
    def __init__(self, server_url):
        self.server_url = server_url

        self.assignment = None
        self.token = None
        self.alias = None
        self.headers = None

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
            self.submitted_folder = os.getcwd() + "/submitted/"+ self.alias

            # Create these folders if does not exit:
            if not os.path.exists(self.source_folder):
                os.makedirs(self.source_folder)
            if not os.path.exists(self.release_folder):
                os.makedirs(self.release_folder)
            if not os.path.exists(self.submitted_folder):
                os.makedirs(self.submitted_folder)

            print("Assignment Loaded:", self.assignment["a_name"])
        else:
            logger.error("AUTH|Server responded with code " + str(response.status_code) + ": " + str(response.content))
            print(response.content)
            raise Exception(response.content)

    def download_nbgrader_submissions(self, filename=None, folder=None):

        # if (filename == None):
        #     filename = self.assignment
        if (folder == None):
            folder = self.alias

        print("Contacting data server")
        try:
            r = requests.get(
                    self.server_url + "/API/download_submission_list/", headers=self.headers)
        except:
            print("Failed to connect with the server, please check your internet connection")
            return False
        print("Parsing received data")
        try:
            data = json.loads(r.content)
        except:
            print("Failed to parse received data")
            print("RAW DATA:", data)
            return False
        print("Found ", len(data), "submitted notebooks.")
        print("Preparing required folder structure")

        # create submitted folder
        if not os.path.exists(os.getcwd() + "/submitted"):
            os.makedirs(os.getcwd() + "/submitted")
        for row in data:
            username = row["username"].replace(" ", "_")

            # create user folder
            if not os.path.exists(os.getcwd() + "/submitted/" + username):
                os.makedirs(os.getcwd() + "/submitted/" + username)
            # create assignment folder
            if not os.path.exists(os.getcwd() + "/submitted/" + username + "/" + folder):
                os.makedirs(os.getcwd() + "/submitted/" + username + "/" + folder)


            # download file
            url = self.server_url + "/Student/get_submission/" + row["f_filename_internal"]
            r = requests.get(url, allow_redirects=True)

            if filename:
                if filename[-5:]!="ipynb":
                    filename = filename + ".ipynb"
            else:
                filename = row["f_filename_original"]

            open(os.getcwd() + "/submitted/" + username + "/" + folder + "/" + filename, 'wb').write(r.content)

            print(f"-> Submission by {username} downloaded successfully")

        print("---All notebooks are ready to be graded!---")

    def download_gradebook(self, autosave=True, download_source=True):
        global observer

        response = requests.get(self.server_url + "/API/get_gradebook", headers=self.headers)
        if response.status_code == 200:
            open(os.getcwd() + "/gradebook.db", 'wb').write(response.content)
            print("Gradebook downloaded")
        elif response.status_code == 404:
            print("Gradebook for does not exists. nbgrader might not work properly.")

        if download_source:
            response = requests.get(self.server_url + "/API/list_files", headers=self.headers)

            if response.status_code == 200:
                files = response.json()
                for file in files:
                    if file["private"]:
                        folder = self.source_folder
                    else:
                        folder = self.release_folder

                    self.download_file(file["file"], folder)

        if autosave:
            event_handler_gradebook = GradebookAutoSaveEventHandler(self)
            observer = Observer()

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

        display(HTML(f"""<a id="btn_source_folder" target="_blank" href="../tree/submitted/{self.alias}" class="btn btn-primary">Open Submissions Folder</a>
        <a id="btn_nbgrader" target="_blank" href="../formgrader" class="btn btn-primary">Open nbgrader</a>"""))

    # def save_results()

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

