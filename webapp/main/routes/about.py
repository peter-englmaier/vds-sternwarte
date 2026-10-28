"""About page with version and build information.

Routes::

    GET  /about  about()  -> about.html
"""
from flask import render_template

from webapp import Config
from webapp.main import main  # blueprint object
from webapp.model.db import SystemParameters


# --------------------------------------------------------------------
# About anzeigen (issue #116 About in Menüleiste)
# --------------------------------------------------------------------
@main.route("/about")
def about():
    """Show version, git commit, environment and the link to the VdS website.

    The values come from :class:`Config` (``APPVERSION``, ``GITCOMMIT``,
    ``CLEANBUILD``, ``ENVIRONMENT``) and the system parameter ``vds_link``.

    .. warning:: ``if [ commit == "" ]`` tests a non-empty list and is always
       true. The commit is therefore always read from the local git repository,
       also when ``GITCOMMIT`` is set. Without a repository (e.g. in Docker),
       the exception is printed and ``GITCOMMIT`` is kept.

    :return: rendered ``about.html``.
    """
    vds_link = SystemParameters.query.filter_by(parameter='vds_link').first()
    commit = Config.GITCOMMIT

    # when running outside docker, we read git commit hash from local git
    if [ commit == "" ]:
            try:
                import git
                repo = git.Repo(search_parent_directories=True)
                commit = repo.head.object.hexsha[0:7]
            except Exception as e:
                print(e)

    if vds_link:
        vds_link = vds_link.value
    else:
        vds_link = "#"
    if Config.APPVERSION != "":
        version = f"{Config.APPVERSION}"
    else:
        version = f"keine"
    isDirty = Config.CLEANBUILD != "true"
    if Config.ENVIRONMENT == "LOCAL":
        server = "Running on your local machine"
    else:
        server = f"{Config.ENVIRONMENT}"
    return render_template('about.html', title='About', vds_link=vds_link, version=version, server=server, commit=commit, isDirty=isDirty)
