#!/usr/bin/env python
from webapp import create_app,db
app=create_app()
ctx=app.app_context()
ctx.push()
db.create_all()
ctx.pop()

print("Database has been initialized")
