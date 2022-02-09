from nbpickup.authoring import Authoring
from nbpickup.submissions import Submissions
from nbpickup.grading import Grading
#from .authoring
from nbpickup.grading import *

# server_url
server_url = "https://nbpickup.org"

authoring = Authoring(server_url)
submissions = Submissions(server_url)
grading = Grading(server_url)



def change_server(server_url):
    """Updates server address for all future API Calls"""
    authoring.server_url = server_url
    submissions.server_url = server_url
    grading.server_url = server_url