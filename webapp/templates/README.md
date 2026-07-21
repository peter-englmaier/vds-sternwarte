# Where are the template files?

To improve project structure, template files are now within the blueprint using them.

For example the `about.html` template moved to `webapp/main/templates/about.html` because it
is only used by the main blueprint.

Templates used in multiple blueprints are still in the global `webapp/templates` folder, 
e.g.`layout.html`

How does it work? The `__init__.py` file of each blueprint now specifies an additional
argument: `template_folder='templates'`. This argument refers to the templates folder 
within the blueprint. 
