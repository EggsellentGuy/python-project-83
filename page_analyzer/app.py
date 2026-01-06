import os
from datetime import datetime
from urllib.parse import urlparse

import requests
import validators
from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from page_analyzer.database import (
    create_check,
    create_url,
    get_url_by_id,
    get_url_id_by_name,
    get_url_name_by_id,
    list_checks_for_url,
    list_urls_with_last_check,
)
from page_analyzer.parser import parse_seo
from page_analyzer.url_normalizer import normalize_url

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")


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
    normalized_url = normalize_url(f"{parsed.scheme}://{parsed.netloc}")
    created_at = datetime.now()

    existing_id = get_url_id_by_name(normalized_url)
    if existing_id is not None:
        url_id = existing_id
        flash("Страница уже существует", "info")
    else:
        url_id = create_url(normalized_url, created_at)
        flash("Страница успешно добавлена", "success")

    return redirect(url_for("url_show", id=url_id))


@app.get("/urls/<int:id>")
def url_show(id):
    url = get_url_by_id(id)
    if url is None:
        abort(404)

    checks = list_checks_for_url(id)
    return render_template("urls/show.html", url=url, checks=checks)


@app.get("/urls")
def urls_index():
    urls = list_urls_with_last_check()
    return render_template("urls/index.html", urls=urls)


@app.post("/urls/<int:id>/checks")
def url_checks_store(id):
    url_name = get_url_name_by_id(id)
    if url_name is None:
        abort(404)

    try:
        response = requests.get(url_name, timeout=10)
        status_code = response.status_code
    except requests.RequestException:
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("url_show", id=id))

    if status_code >= 500:
        flash("Произошла ошибка при проверке", "danger")
        return redirect(url_for("url_show", id=id))

    try:
        h1_text, title_text, description_text = parse_seo(response.text)
    except Exception:
        h1_text = None
        title_text = None
        description_text = None

    created_at = datetime.now()
    create_check(
        id,
        status_code,
        h1_text,
        title_text,
        description_text,
        created_at,
    )

    flash("Страница успешно проверена", "success")
    return redirect(url_for("url_show", id=id))
