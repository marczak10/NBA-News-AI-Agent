from datetime import datetime
import html
import logging
import os
import smtplib
import time

import markdown
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.agents.email_agent import EmailAgent, EmailIntroduction
from app.services.env_config import load_project_env
from app.steps.base import RankedSummary, State

load_project_env()

logger = logging.getLogger(__name__)


def _render_markdown(text: str) -> str:
    return markdown.markdown(text.strip(), extensions=["nl2br"])


def _wrap_email_html(content: str) -> str:
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333333;
            max-width: 680px;
            margin: 0 auto;
            padding: 24px;
            background-color: #ffffff;
        }}
        h1 {{
            font-size: 24px;
            font-weight: 700;
            color: #111111;
            margin: 0 0 12px;
        }}
        h2 {{
            font-size: 18px;
            font-weight: 600;
            color: #111111;
            margin: 24px 0 12px;
        }}
        h3 {{
            font-size: 16px;
            font-weight: 600;
            color: #111111;
            margin: 0 0 8px;
            line-height: 1.4;
        }}
        p {{
            margin: 8px 0;
            color: #4a4a4a;
        }}
        strong {{
            font-weight: 600;
            color: #111111;
        }}
        em {{
            font-style: italic;
            color: #666666;
        }}
        a {{
            color: #0066cc;
            text-decoration: none;
            font-weight: 500;
        }}
        hr {{
            border: none;
            border-top: 1px solid #e5e5e5;
            margin: 20px 0;
        }}
        .greeting p {{
            margin-top: 0;
        }}
        .introduction p {{
            margin: 0;
        }}
        .article {{
            margin: 20px 0;
        }}
        .article p {{
            margin: 6px 0;
        }}
        .article-link {{
            display: inline-block;
            margin-top: 8px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
{content}
</body>
</html>"""


def markdown_to_html(markdown_text: str) -> str:
    return _wrap_email_html(_render_markdown(markdown_text))


def _build_email_text(
    top_ranked_summaries: list[RankedSummary],
    introduction: EmailIntroduction,
    current_date: str,
) -> str:
    lines = [
        "AI NBA News Daily Summary",
        "",
        introduction.greeting.strip(),
        introduction.introduction.strip(),
        "",
        f"Top {len(top_ranked_summaries)} NBA News Articles for {current_date}",
        "",
    ]

    for item in top_ranked_summaries:
        lines.append(f"{item['rank']}. {item['title']}")
        lines.append(item["summary"].strip())
        if item.get("url"):
            lines.append(f"Read more: {item['url']}")
        lines.append("")

    return "\n".join(lines).strip()


def _build_email_html(
    top_ranked_summaries: list[RankedSummary],
    introduction: EmailIntroduction,
    current_date: str,
) -> str:
    article_sections = []
    for item in top_ranked_summaries:
        article_html = [
            '<section class="article">',
            f"<h3>{item['rank']}. {html.escape(item['title'])}</h3>",
            _render_markdown(item["summary"]),
        ]
        if item.get("url"):
            article_html.append(
                f'<p><a href="{html.escape(item["url"])}" class="article-link">Read more</a></p>'
            )
        article_html.append("</section>")
        article_sections.append("\n".join(article_html))

    html_parts = [
        "<h1>AI NBA News Daily Summary</h1>",
        f'<div class="greeting">{_render_markdown(introduction.greeting)}</div>',
        f'<div class="introduction">{_render_markdown(introduction.introduction)}</div>',
        f"<h2>Top {len(top_ranked_summaries)} NBA News Articles for {html.escape(current_date)}</h2>",
    ]
    if article_sections:
        html_parts.append("<hr>")
        html_parts.append("\n<hr>\n".join(article_sections))

    return _wrap_email_html("\n".join(html_parts))


def digest_to_html(digest_response: object) -> str:
    if hasattr(digest_response, "to_markdown"):
        return markdown_to_html(digest_response.to_markdown())
    return markdown_to_html(str(digest_response))


def _send_email(
    subject: str,
    body_text: str,
    body_html: str,
    recipients: list[str] | None,
) -> None:
    sender_email = os.getenv("MY_EMAIL")
    app_password = os.getenv("APP_PASSWORD")

    if recipients is None:
        if not sender_email:
            raise ValueError("MY_EMAIL environment variable is not set")

        recipients = [sender_email]

    recipients = [r for r in recipients if r is not None]
    if not recipients:
        raise ValueError("No valid recipients provided")

    if not sender_email:
        raise ValueError("MY_EMAIL environment variable is not set")
    if not app_password:
        raise ValueError("APP_PASSWORD environment variable is not set")

    logger.info("Sending email to %s recipient(s).", len(recipients))

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = ", ".join(recipients)

    part1 = MIMEText(body_text, "plain", "utf-8")
    message.attach(part1)

    if body_html:
        part2 = MIMEText(body_html, "html", "utf-8")
        message.attach(part2)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipients, message.as_string())

    logger.info("Email sent successfully.")


def email(state: State) -> State:
    logger.info("Starting email step.")
    email_start_time = time.time()
    top_summaries = state.get("top_summaries", [])
    if not top_summaries:
        logger.info("Skipping email step because there are no top summaries.")
        return {}

    email_agent = EmailAgent()
    email_introduction = email_agent.generate_email_introduction(top_summaries)

    reference_time = state.get("start_time") or datetime.now()
    current_date = reference_time.strftime("%B %d, %Y")
    subject = f"AI NBA News Daily Summary - {current_date}"
    email_text = _build_email_text(top_summaries, email_introduction, current_date)
    email_html = _build_email_html(top_summaries, email_introduction, current_date)

    _send_email(
        subject=subject,
        body_text=email_text,
        body_html=email_html,
        recipients=(
            os.getenv("EMAIL_RECIPIENTS", "").split(",")
            if os.getenv("EMAIL_RECIPIENTS")
            else None
        ),
    )

    email_end_time = time.time()
    logger.info(
        "Finished email step in %.2f seconds.",
        email_end_time - email_start_time,
    )

    return {
        "email_html": email_html,
        "email_introduction": {
            "greeting": email_introduction.greeting,
            "introduction": email_introduction.introduction,
        },
    }
