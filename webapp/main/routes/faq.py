"""FAQ page.

Routes::

    GET  /faq  faq()  -> faq.html
"""
from flask import render_template

from webapp.main import main  # blueprint object
from webapp.model.db import SystemParameters


# --------------------------------------------------------------------
# FAQ anzeigen
# --------------------------------------------------------------------
@main.route("/faq")
def faq():
    """Show the FAQ with the link to the VdS website.

    The link comes from the system parameter ``vds_link``, default ``#``.

    :return: rendered ``faq.html``.
    """
    vds_link = SystemParameters.query.filter_by(parameter='vds_link').first()
    if vds_link:
        vds_link = vds_link.value
    else:
        vds_link = "#"
    return render_template('faq.html', title='FAQ', vds_link=vds_link)
