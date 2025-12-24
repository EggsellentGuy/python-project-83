import os

import psycopg
from psycopg.rows import dict_row


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    return psycopg.connect(database_url, row_factory=dict_row)


def get_url_id_by_name(name: str):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM urls WHERE name = %s", (name,))
            row = cur.fetchone()
            return None if row is None else row["id"]


def create_url(name: str, created_at):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO urls (name, created_at)
                VALUES (%s, %s)
                RETURNING id
                """,
                (name, created_at),
            )
            return cur.fetchone()["id"]


def get_url_by_id(url_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, created_at FROM urls WHERE id = %s",
                (url_id,),
            )
            return cur.fetchone()


def get_url_name_by_id(url_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name FROM urls WHERE id = %s", (url_id,))
            row = cur.fetchone()
            return None if row is None else row["name"]


def list_urls_with_last_check():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    urls.id,
                    urls.name,
                    urls.created_at,
                    last_check.created_at AS last_check_at,
                    last_check.status_code AS last_status_code
                FROM urls
                LEFT JOIN LATERAL (
                    SELECT created_at, status_code
                    FROM url_checks
                    WHERE url_checks.url_id = urls.id
                    ORDER BY created_at DESC
                    LIMIT 1
                ) AS last_check ON TRUE
                ORDER BY urls.id DESC
                """
            )
            return cur.fetchall()


def list_checks_for_url(url_id: int):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, status_code, h1, title, description, created_at
                FROM url_checks
                WHERE url_id = %s
                ORDER BY id DESC
                """,
                (url_id,),
            )
            return cur.fetchall()


def create_check(url_id: int,
                 status_code: int,
                 h1,
                 title,
                 description,
                 created_at,
                 ):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO url_checks (
                    url_id,
                    status_code,
                    h1,
                    title,
                    description,
                    created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (url_id, status_code, h1, title, description, created_at),
            )
