# Import Python libs
from os import path
import re

# Import Odoo libs
from odoo.addons.queue_job.jobrunner.runner import QueueJobRunner, Database
from odoo.tools import config
from contextlib import closing


# ==================================================================
# Monkey patch OCA module's `get_db_names` method
# ==================================================================
# OLD_GET_DB_NAMES = QueueJobRunner.get_db_names


# def new_get_db_names(self):
#     """
#     Filter database names based on the `dbfilter`configuration value
#     if the `db_name` config was not set
#     """
#     db_names = OLD_GET_DB_NAMES(self)

#     if not config["db_name"]:
#         dbfilter = config["dbfilter"]
#         db_names = [name for name in db_names if re.match(dbfilter, name)]

#     return db_names


# QueueJobRunner.get_db_names = new_get_db_names

# ==================================================================
# Monkey patch OCA module's `initialize_databases` method
# ==================================================================

OLD_INITIALIZE_DATABASES = QueueJobRunner.initialize_databases


def new_initialize_databases(self):
    """
    Solve the existing issue issue: https://github.com/OCA/queue/tree/17.0/queue_job#known-issues-roadmap
    Based on this suggested solution: https://github.com/OCA/queue/issues/386
    """
    for db_name in self.get_db_names():
        db = Database(db_name)
        with closing(db.conn.cursor()) as cr:
            query = """
            UPDATE queue_job qj
            SET state = 'pending'
            WHERE qj.id IN (
                SELECT id
                FROM queue_job
                WHERE state IN ('started', 'enqueued')
                FOR UPDATE SKIP LOCKED
                )
            """
            cr.execute(query)
    return OLD_INITIALIZE_DATABASES(self)


QueueJobRunner.initialize_databases = new_initialize_databases
