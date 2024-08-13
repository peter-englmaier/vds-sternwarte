#!/usr/bin/env python
from webapp import create_app

app = create_app()
ctx=app.app_context()
ctx.push()

#-------------
# create a schema diagram plot

from sqlalchemy_schemadisplay import create_schema_graph
from sqlalchemy import MetaData
from webapp import db


graph = create_schema_graph(
		engine=db.engine,
		metadata=db.metadata,
		show_datatypes=False,
		concentrate=False
)
graph.write_svg('docs/model-diagram.svg')

#-------------
# create a UML diagram plot

from sqlalchemy_schemadisplay import create_uml_graph
from sqlalchemy.orm import class_mapper
from webapp import models

# lets find all the mappers in our model
model = models
mappers = []
for attr in dir(model):
    if attr[0] == '_': continue
    try:
        cls = getattr(model, attr)
        mappers.append(class_mapper(cls))
    except Exception:
        pass

# pass them to the function and set some formatting options
graph = create_uml_graph(mappers,
    show_operations=False, # not necessary in this case
    show_multiplicity_one=False # some people like to see the ones, some don't
)
graph.write_svg('docs/uml-diagram.svg') # write out the file
