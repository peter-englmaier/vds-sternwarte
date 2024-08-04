#!/bin/bash
if [ "$1" == "" ]; then
  flask --help
else
  flask --app run.py "$@"
fi
