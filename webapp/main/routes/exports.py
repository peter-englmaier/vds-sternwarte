"""Export data for statistic analysis.

Routes::

    GET  /exports  exports()  -> exports.html
"""
from flask import render_template

from webapp import Config
from webapp.main import main  # blueprint object
from webapp.model.db import SystemParameters


# --------------------------------------------------------------------
# Export
# --------------------------------------------------------------------
@main.route("/exports")
def exports():
    """Allow  download of data for statistical purposees.

    The values come from :class:`Config` (``APPVERSION``, ``GITCOMMIT``,
    ``CLEANBUILD``, ``ENVIRONMENT``) and the system parameter ``vds_link``.

    .. warning:: ``if [ commit == "" ]`` tests a non-empty list and is always
       true. The commit is therefore always read from the local git repository,
       also when ``GITCOMMIT`` is set. Without a repository (e.g. in Docker),
       the exception is printed and ``GITCOMMIT`` is kept.

    :return: rendered ``about.html``.
    """
    pass
    return render_template('exports.html', title='Export')
