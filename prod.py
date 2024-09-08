#!/usr/bin/env python

from webapp import create_app
import os

print("STARTING PRODUCTION SERVER")

app = create_app()

from waitress import serve
from paste.translogger import TransLogger
# see: https://docs.pylonsproject.org/projects/waitress/en/stable/arguments.html
serve(TransLogger(app, setup_console_handler=False), 
    listen='*:5000', 
    url_scheme='https',
    threads=4,
    trusted_proxy=os.environ.get('TRUSTED_PROXY'),
    log_untrusted_proxy_headers=True
    )
