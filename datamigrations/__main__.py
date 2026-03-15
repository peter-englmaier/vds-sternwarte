import sys, importlib
mig=sys.argv[1]
module=importlib.import_module("datamigrations."+mig)
module.upgrade()
