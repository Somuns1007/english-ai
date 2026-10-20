"""TLS-only SMTP delivery; credentials come from environment and never enter responses/logs."""
import os
import smtplib
import ssl
from email.message import EmailMessage


def configured():
    return (all(os.getenv(key) for key in ('AUTH_SMTP_HOST', 'AUTH_SMTP_USER', 'AUTH_SMTP_PASSWORD', 'AUTH_MAIL_FROM'))
            and os.getenv('AUTH_SMTP_SECURITY', 'ssl') in ('ssl', 'starttls'))


def send_code(email: str, code: str, purpose: str):
    message = EmailMessage()
    message['From'] = os.environ['AUTH_MAIL_FROM']
    message['To'] = email
    message['Subject'] = '阿Q的英语自习室 · 邮箱验证码'
    action = '注册验证' if purpose == 'register' else '重置密码'
    message.set_content(f'你正在进行{action}。\n\n验证码：{code}\n\n10 分钟内有效，仅可使用一次。'
                        '\n不要向他人透露验证码。如果不是你本人操作，请忽略此邮件。')
    mode = os.getenv('AUTH_SMTP_SECURITY', 'ssl')
    port = int(os.getenv('AUTH_SMTP_PORT', '465' if mode == 'ssl' else '587'))
    context = ssl.create_default_context()
    if mode == 'ssl':
        client = smtplib.SMTP_SSL(os.environ['AUTH_SMTP_HOST'], port, timeout=10, context=context)
    elif mode == 'starttls':
        client = smtplib.SMTP(os.environ['AUTH_SMTP_HOST'], port, timeout=10)
    else:
        raise ValueError('TLS is required')
    with client:
        if mode == 'starttls':
            client.ehlo()
            client.starttls(context=context)
            client.ehlo()
        client.login(os.environ['AUTH_SMTP_USER'], os.environ['AUTH_SMTP_PASSWORD'])
        client.send_message(message)
