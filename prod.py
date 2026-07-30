#!/usr/bin/env python

from webapp import create_app
import os

print("STARTING PRODUCTION SERVER")

app = create_app()

from waitress import serve
from paste.translogger import TransLogger


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ('true', '1', 't')


# see: https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html
waitress_options = {
    'listen': os.getenv('LISTEN', '0.0.0.0:5000'),
    'url_scheme': os.getenv('URL_SCHEMA', 'https'),
    'threads': int(os.getenv('THREADS', '4')),
}

trusted_proxy = os.getenv('TRUSTED_PROXY')
if trusted_proxy:
    waitress_options.update({
        'trusted_proxy': trusted_proxy,
        'trusted_proxy_count': int(os.getenv('TRUSTED_PROXY_COUNT', '1')),
        'trusted_proxy_headers': os.getenv(
            'TRUSTED_PROXY_HEADERS',
            'x-forwarded-for x-forwarded-host x-forwarded-proto x-forwarded-port',
        ),
        'log_untrusted_proxy_headers': env_bool('LOG_UNTRUSTED_PROXY_HEADERS', True),
    })

serve(
    TransLogger(app, setup_console_handler=env_bool('SETUP_CONSOLE_HANDLER', False)),
    **waitress_options,
)
