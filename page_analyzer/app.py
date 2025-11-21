import os
from datetime import datetime
from urllib.parse import urlparse
from psycopg.rows import dict_row

import psycopg
import validators
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, abort


load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/urls")
def urls_store():
    url = request.form.get("url", "").strip()

    errors = []

    if not url:
        errors.append("URL не должен быть пустым")
    elif len(url) > 255:
        errors.append("URL не должен превышать 255 символов")
    elif not validators.url(url):
        errors.append("Некорректный URL")

    if errors:
        for message in errors:
            flash(message, "danger")
        return render_template("index.html"), 422

    parsed = urlparse(url)
    normalized_url = f"{parsed.scheme}://{parsed.netloc}"

    created_at = datetime.now()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM urls WHERE name = %s",
                (normalized_url,),
            )
            existing = cur.fetchone()

            if existing:
                url_id = existing["id"]
                flash("Страница уже существует", "info")
            else:
                cur.execute(
                    """
                    INSERT INTO urls (name, created_at)
                    VALUES (%s, %s)
                    RETURNING id
                    """,
                    (normalized_url, created_at),
                )
                url_id = cur.fetchone()["id"]
                flash("Страница успешно добавлена", "success")

    return redirect(url_for("url_show", id=url_id))


@app.get("/urls/<int:id>")
def url_show(id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, name, created_at FROM urls WHERE id = %s",
                (id,),
            )
            url = cur.fetchone()

    if url is None:
        abort(404)

    return render_template("urls/show.html", url=url)


@app.get("/urls")
def urls_index():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, created_at
                FROM urls
                ORDER BY id DESC
                """
            )
            urls = cur.fetchall()

    return render_template("urls/index.html", urls=urls)
