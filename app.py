#!/usr/bin/env python
import os
import sys

if sys.version_info.major < 3:
    print("Cannot run with python 2")
    exit(1)

# the reloader's serving child (WERKZEUG_RUN_MAIN=true) is restarted on every code change;
# print version info only once, in the initial process
if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
    py_version=f"{sys.version_info.major}.{sys.version_info.minor}"
    print(f"Python Version: {py_version}.{sys.version_info.micro}")

    py_version_recommended="3.14"
    if py_version != py_version_recommended:
        print("WARNING: ------------------------------------------------")
        print(f"WARNING: not running with recommended python version {py_version_recommended}")
        print("WARNING: ------------------------------------------------")


from webapp import create_app, init_users

app = create_app()

if __name__ == '__main__':
    # with debug=True the reloader runs this script twice: a watcher process and the
    # serving child (WERKZEUG_RUN_MAIN=true). Only the serving child needs the database.
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        init_users(app)
    app.run(debug=True)
