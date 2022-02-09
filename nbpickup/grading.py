import logging
import os
import requests
import json

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

    def download_nbgrader_submissions(self, token=None, group=None, filename=None, folder=None):

        if (filename == None):
            filename = self.assignment
        if (folder == None):
            folder = self.assignment

        print("Contacting data server")
        try:
            if group == None:
                r = requests.get(self.server_url + "/API/download_list/", headers=self.headers)
            else:
                r = requests.get(
                    self.server_url + "/API/download_list/", headers=self.headers)
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
            # create user folder
            if not os.path.exists(os.getcwd() + "/submitted/" + row["u_name"].replace(" ", "_")):
                os.makedirs(os.getcwd() + "/submitted/" + row["u_name"].replace(" ", "_"))
            # create assignment folder
            if not os.path.exists(os.getcwd() + "/submitted/" + row["u_name"].replace(" ", "_") + "/" + folder):
                os.makedirs(os.getcwd() + "/submitted/" + row["u_name"].replace(" ", "_") + "/" + folder)

            # download file
            url = self.server_url + "/uploads/" + row["s_filename"]
            r = requests.get(url, allow_redirects=True)
            open(os.getcwd() + "/submitted/" + row["u_name"].replace(" ",
                                                                     "_") + "/" + folder + "/" + filename + ".ipynb",
                 'wb').write(r.content)

            print("Assignment saved successfully")

        print("Notebook are ready to be graded")

    # def autosave()

    # def save_results()
