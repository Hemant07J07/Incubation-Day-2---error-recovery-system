import os
import smtplib
import requests
from email.mime.text import MIMEText

def send_email(smtp_host, smtp_port, username, password, to_emails, subject, body):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = username
    msg['To'] = ", ".join(to_emails if isinstance(to_emails, list) else [to_emails])

    s = smtplib.SMTP(smtp_host, smtp_port, timeout = 10)
    s.starttls()
    s.login(username, password)
    s.sendmail(username, to_emails, msg.as_string())
    s.quit()

def send_telegram(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    r = requests.post(url, json=payload, timeout=10)
    return r.ok

def post_webhook(webhook_url, payload):
    r = requests.post(webhook_url, json=payload, timeout=10)
    return r.ok

def notify_all(cfg, subject, message):
    """
    cfg: portion of config (alerts/email/telegram/webhook) or env fallback
    
    """
    try:
        if cfg.get("email", {}).get("enabled", False):
            smtp_host = os.getenv("SMTP_HOST")
            smtp_port = int(os.getenv("SMTP_PORT", 587))
            smtp_user = os.getenv("SMTP_USER")
            smtp_pass = os.getenv("SMTP_PASS")
            to = cfg.get("email", {}).get("to", [])
            if smtp_host and smtp_user and smtp_pass and to:
                send_email(smtp_host, smtp_port, smtp_user, smtp_pass, to, subject, message)
    
    except Exception as e:
        print("Email notify failed:", e)
    
    # Telegram
    try:
        if cfg.get("telegram", {}).get("enabled", False):
            token = os.getenv("TELEGRAM_BOT_TOKEN")
            chat_id = os.getenv("TELEGRAM_CHAT_ID") or cfg.get("telegram", {}).get("chat_id")
            if token and chat_id:
                send_telegram(token, chat_id, message)

    except Exception as e:
        print("Telegram notify failed:", e)

    # Webhook
    try:
        if cfg.get("webhook", {}).get("enabled", False):
            webhook_url = os.getenv("WEBHOOK_URL") or cfg.get("webhook", {}).get("url")
            if webhook_url:
                post_webhook(webhook_url, {"subject": subject, "message": message})
    except Exception as e:
        print("Webhook notify failed:", e)