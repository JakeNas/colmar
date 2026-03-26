#!/usr/bin/env python3
"""Daily news summary emailer.

Fetches top headlines on AI, product strategy, product management, and Accenture,
then sends a formatted HTML digest via Gmail SMTP.

Required environment variables:
  GMAIL_USER         - Your Gmail address (sender and recipient)
  GMAIL_APP_PASSWORD - Gmail App Password (not your account password)
  NEWSAPI_KEY        - API key from https://newsapi.org (free tier works)
"""

import os
import smtplib
import sys
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import urlopen
from urllib.parse import urlencode
from urllib.error import URLError
import json

NEWSAPI_BASE = "https://newsapi.org/v2/everything"

TOPICS = [
    {"label": "Artificial Intelligence", "query": "artificial intelligence OR generative AI OR LLM"},
    {"label": "Product Management", "query": "product management OR product manager OR product roadmap"},
    {"label": "Product Strategy", "query": "product strategy OR go-to-market OR product led growth"},
    {"label": "Accenture", "query": "Accenture"},
]

MAX_ARTICLES_PER_TOPIC = 5


def fetch_articles(query: str, api_key: str) -> list[dict]:
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": MAX_ARTICLES_PER_TOPIC,
        "apiKey": api_key,
    }
    url = f"{NEWSAPI_BASE}?{urlencode(params)}"
    try:
        with urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        return data.get("articles", [])
    except (URLError, json.JSONDecodeError) as exc:
        print(f"Warning: could not fetch articles for '{query}': {exc}", file=sys.stderr)
        return []


def build_html(sections: list[dict]) -> str:
    today = date.today().strftime("%A, %B %-d, %Y")

    topic_html_parts = []
    for section in sections:
        articles_html = ""
        for art in section["articles"]:
            title = art.get("title") or "Untitled"
            url = art.get("url") or "#"
            description = art.get("description") or ""
            source = (art.get("source") or {}).get("name") or ""
            published = (art.get("publishedAt") or "")[:10]

            meta = " &middot; ".join(filter(None, [source, published]))
            desc_block = f"<p style='margin:4px 0 0;color:#555;font-size:13px;'>{description}</p>" if description else ""

            articles_html += f"""
            <div style='margin-bottom:18px;padding-bottom:14px;border-bottom:1px solid #eee;'>
              <a href='{url}' style='font-size:15px;font-weight:600;color:#1a1a1a;text-decoration:none;'>{title}</a>
              {desc_block}
              <p style='margin:4px 0 0;font-size:12px;color:#999;'>{meta}</p>
            </div>"""

        if not articles_html:
            articles_html = "<p style='color:#999;font-size:13px;'>No articles found today.</p>"

        topic_html_parts.append(f"""
        <div style='margin-bottom:32px;'>
          <h2 style='font-size:18px;color:#2563eb;margin:0 0 12px;border-left:4px solid #2563eb;padding-left:10px;'>
            {section['label']}
          </h2>
          {articles_html}
        </div>""")

    body = "\n".join(topic_html_parts)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset='utf-8'></head>
<body style='font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;max-width:680px;margin:0 auto;padding:24px;background:#f9fafb;'>
  <div style='background:#fff;border-radius:10px;padding:32px;box-shadow:0 1px 4px rgba(0,0,0,.08);'>
    <h1 style='font-size:22px;margin:0 0 4px;color:#111;'>Your Daily News Digest</h1>
    <p style='margin:0 0 28px;color:#888;font-size:14px;'>{today}</p>
    {body}
    <hr style='border:none;border-top:1px solid #eee;margin:24px 0 16px;'>
    <p style='font-size:12px;color:#bbb;margin:0;'>Powered by NewsAPI &middot; Topics: AI, Product Management, Product Strategy, Accenture</p>
  </div>
</body>
</html>"""


def send_email(html: str, gmail_user: str, app_password: str) -> None:
    today = date.today().strftime("%b %-d, %Y")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Daily News Digest - {today}"
    msg["From"] = gmail_user
    msg["To"] = gmail_user
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, app_password)
        server.sendmail(gmail_user, gmail_user, msg.as_string())


def main() -> None:
    gmail_user = os.environ.get("GMAIL_USER")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    newsapi_key = os.environ.get("NEWSAPI_KEY")

    missing = [v for v, k in [("GMAIL_USER", gmail_user), ("GMAIL_APP_PASSWORD", app_password), ("NEWSAPI_KEY", newsapi_key)] if k is None]
    if missing:
        print(f"Error: missing environment variables: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)

    print("Fetching news articles...")
    sections = []
    for topic in TOPICS:
        articles = fetch_articles(topic["query"], newsapi_key)
        sections.append({"label": topic["label"], "articles": articles})
        print(f"  {topic['label']}: {len(articles)} articles")

    html = build_html(sections)

    print(f"Sending email to {gmail_user}...")
    send_email(html, gmail_user, app_password)
    print("Done! Email sent successfully.")


if __name__ == "__main__":
    main()
