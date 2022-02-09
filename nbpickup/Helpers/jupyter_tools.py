from IPython.display import display, Javascript, HTML, IFrame

def save_notebook(silent = False):
    """
    Outputs javascript to perform SAVE action on the notebook. Important to make sure that we are submitting
    final version of Jupyter notebook file.
    """
    display(Javascript("IPython.notebook.save_notebook()"), include=['application/javascript'])
    if not silent:
        print("Autosaving notebook...")


def jupyter_file_location():
    """
    Function to get location of current jupyter notebook file
    Source: https://github.com/jupyter/notebook/issues/1000#issuecomment-359875246
    """
    import json
    import os.path
    import re
    import ipykernel
    import requests

    # Alternative that works for both Python 2 and 3:
    from requests.compat import urljoin

    try:  # Python 3 (see Edit2 below for why this may not work in Python 2)
        from notebook.notebookapp import list_running_servers
    except ImportError:  # Python 2
        import warnings
        from IPython.utils.shimmodule import ShimWarning
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=ShimWarning)
            from IPython.html.notebookapp import list_running_servers

    """
    Return the full path of the jupyter notebook.
    """
    kernel_id = re.search('kernel-(.*).json',
                          ipykernel.connect.get_connection_file()).group(1)
    servers = list_running_servers()
    for ss in servers:
        response = requests.get(urljoin(ss['url'], 'api/sessions'),
                                params={'token': ss.get('token', '')})
        for nn in json.loads(response.text):
            if nn['kernel']['id'] == kernel_id:
                relative_path = nn['notebook']['path']
                return os.path.join(ss['notebook_dir'], relative_path)

    return False