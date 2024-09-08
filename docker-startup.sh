#!/bin/sh
flask db upgrade
#exec gunicorn prod:app -b 0.0.0.0:5000 -w 1 --access-logfile -
exec waitress-serv --listen 0.0.0.0:5000 app:app

