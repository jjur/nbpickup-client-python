from .authoring import Authoring
#from .authoring
from .grading import *

# server_url
server_url = "https://nbpickup.org"

authoring = Authoring(server_url)



def change_server(server_url):
    """Updates server address for all future API Calls"""
    authoring.server_url = server_url