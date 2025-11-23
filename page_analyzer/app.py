import os
from datetime import datetime
from urllib.parse import urlparse
from psycopg.rows import dict_row

import psycopg
import validators
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    abort,
)


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

            cur.execute(
                """
                SELECT id, status_code, h1, title, description, created_at
                FROM url_checks
                WHERE url_id = %s
                ORDER BY id DESC
                """,
                (id,),
            )
            checks = cur.fetchall()

    return render_template("urls/show.html", url=url, checks=checks)


@app.get("/urls")
def urls_index():
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
            urls = cur.fetchall()

    return render_template("urls/index.html", urls=urls)


@app.post("/urls/<int:id>/checks")
def url_checks_store(id):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT name FROM urls WHERE id = %s",
                (id,),
            )
            row = cur.fetchone()

    if row is None:
        abort(404)

    url_name = row["name"]

    try:
        response = requests.get(url_name, timeout=10)
        status_code = response.status_code
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("url_show", id=id))

    if status_code >= 500:
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("url_show", id=id))

    h1_text = None
    title_text = None
    description_text = None

    try:
        soup = BeautifulSoup(response.text, "html.parser")
        h1_tag = soup.find("h1")
        if h1_tag:
            h1_text = h1_tag.get_text(strip=True)

        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)

        meta_desc_tag = soup.find("meta", attrs={"name": "description"})
        if meta_desc_tag and meta_desc_tag.get("content"):
            description_text = meta_desc_tag["content"].strip()
    except Exception:
        pass

    created_at = datetime.now()

    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO url_checks (
                url_id, status_code, h1, title, description, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (id, status_code, h1_text, title_text,
                 description_text, created_at),
            )

    flash("Страница успешно проверена", "success")
    return redirect(url_for("url_show", id=id))
