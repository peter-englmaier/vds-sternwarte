#!/bin/sh
flask db upgrade
exec python prod.py
