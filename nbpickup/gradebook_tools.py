from nbgrader.api import Gradebook, MissingEntry
import os
from sqlite3 import OperationalError


def get_gradebook_content_stats(filename, path):
    """Reads the Gradebook file with nbgrader API to determine the number of assignments and students in the db."""
    try:
        # Try reading absolute path
        with Gradebook('sqlite:////' + os.path.join(path, filename)) as gb:
            num_students = len(gb.students)
            num_assignments = len(gb.assignments)
    except OperationalError:
        with Gradebook('sqlite:///gradebook.db') as gb:
            num_students = len(gb.students)
            num_assignments = len(gb.assignments)

    return num_assignments, num_students