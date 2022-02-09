import requests
import re
from nbpickup.Helpers.jupyter_tools import save_notebook, jupyter_file_location
import time
import logging
import urllib.parse

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


class Submissions():
    def __init__(self, server_url, assignment_files=None, email=None):
        self.email = None
        self.assignment_files = None

        self.server_url = server_url

        if assignment_files:
            self.assignment_files = assignment_files
        if email:
            self.email = email



    def set_email(self, email):
        """Verifies if valid email is provided and sets it for future submission"""
        if (re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email)):
            self.email = email
            return True
        else:
            print("Provided Email is not Valid")
            return False


    def submit_ipynb(self, assignment_alias, autosave_timer = 5):
        """
        Submits single jupyter notebook file
        TODO: Add support for multiple files.
        """

        # Check if user provided an email
        if not self.email:
            print("User email is missing")
        # TODO: Dealing with case of anonymous submissions

        # Autosaving
        try:
            save_notebook()
            time.sleep(autosave_timer)
        except Exception as e:
            print("Autosave Failed, please make sure your file is saved.")
            print("ERR"+repr(e))
            logger.exception("Err"+repr(e))
        else:
            print("Notebook saved.")

        filename = None
        try:
            filename = jupyter_file_location()
        except Exception as e:
            print("Autosave Failed, please make sure your file is saved.")
            print("ERR" + repr(e))
            logger.exception("Err" + repr(e))

        # Attempt to submit notebook
        if filename:
            # We successfully obtained filename, therefore we can submit the notebook without any issues
            files = {'file': open(filename, 'rb')}
            values = {'email': self.email}
            r = requests.post(self.server_url + "/Student_api/submit_one/" + assignment_alias, files=files, data=values)

            if r.status_code == 200:
                print("Assingment Submitted Successfully.")
                print(r.text)
            else:
                print("Automatic Assignemnt Submission Faied. Reason:", r.text)
                print("Please use the following form to submit instead:")
                filename=False

        if not filename:
            # Plan B
            src = self.server_url + "/student/submit_minimal/" + assignment_alias + "/" + urllib.parse.quote(self.email)
            from IPython.display import display, IFrame
            display(IFrame(src, 630, 200))






    # def submit_py( autosave=False):


    # def submit_all( allowed_file_extentions)


    # def submit_cocalc()


    # def submit_deepnote()


