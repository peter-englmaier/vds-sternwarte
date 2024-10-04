#!/bin/sh
import app


print("DEPRECATED: use ./app.py instead of ./run.py")
exec(open('app.py').read())

