from nbgrader.api import Gradebook, MissingEntry
import os
from sqlite3 import OperationalError
from sqlalchemy.exc import OperationalError as OE


def get_gradebook_content_stats(filename, path):
    """Reads the Gradebook file with nbgrader API to determine the number of assignments and students in the db."""
    try:
        # Try reading absolute path
        with Gradebook('sqlite:////' + os.path.join(path, filename)) as gb:
            num_students = len(gb.students)
            num_assignments = len(gb.assignments)
    except (OperationalError, OE):
        try:
            with Gradebook('sqlite:///gradebook.db') as gb:
                num_students = len(gb.students)
                num_assignments = len(gb.assignments)
        except (OperationalError, OE):
            return -1, -1

    return num_assignments, num_students