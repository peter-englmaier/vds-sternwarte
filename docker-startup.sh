#!/bin/sh
echo "Running docker-startup.sh"
export FLASK_APP=prod.py

if [ "$RUNCELERY" == "true" ]; then
  if [ "$RUNFLASK" == "true" ]; then
    echo "Run celery worker in background"
    celery -A make_celery worker -l info &
  else
    echo "Run celery worker"
    exec celery -A make_celery worker -l info
  fi
fi

if [ "$RUNBEAT" == "true" ]; then
  if [ "$RUNFLASK" == "true" ]; then
    echo "Run celery beat in background"
    celery -A make_celery beat -l info -s instance/celerybeat-schedule  &
  else
    echo "Run celery beat"
    exec celery -A make_celery beat -l info -s instance/celerybeat-schedule
  fi
fi

if [ "$RUNFLASK" == "true" ]; then
  echo "Upgrade database if needed"
  flask --app app.py db upgrade

  echo "Run flask app"
  exec flask --app prod.py run
fi
