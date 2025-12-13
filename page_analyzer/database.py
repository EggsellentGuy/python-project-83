import os

import psycopg
from psycopg.rows import dict_row


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    return psycopg.connect(database_url, row_factory=dict_row)
