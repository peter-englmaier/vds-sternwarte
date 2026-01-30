#!/bin/sh -x
python --version
flask --app app.py db upgrade
cat prod.py
exec python prod.py
