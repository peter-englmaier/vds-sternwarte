"""Occupancy calendar.

Routes::

    GET  /orders/show_calendar  show_calendar()  -> calendar.html, _calendar.html (HTMX)
"""
from datetime import date, datetime

from flask import render_template, request
from flask_login import login_required

from webapp.orders import orders  # blueprint object
from webapp.orders.orderservices import calendar_service
from webapp.users.utils import role_required


# --------------------------------------------------------------------
# Belegungskalender anzeigen
# --------------------------------------------------------------------
@orders.route("/orders/show_calendar", methods=["GET"])
@login_required
@role_required("user")
def show_calendar():
    """Show the occupancy calendar of one month.

    Shows planned and approved days and the moon phases. Query parameters:

    * ``year``, ``month``: month to show, default is the current month.
    * ``picker``: show the calendar as date picker.
    * ``target_id``, ``display_id``: ids of the input and display elements the
      date picker fills.

    For HTMX requests, only the partial ``_calendar.html`` is rendered.

    :return: rendered ``calendar.html`` or ``_calendar.html``.
    """
    year = request.args.get("year", default=datetime.now().year, type=int)
    month = request.args.get("month", default=datetime.now().month, type=int)
    picker = request.args.get("picker", default=False, type=bool)
    target_id = request.args.get("target_id", default="request_date", type=str)
    display_id = request.args.get("display_id", default="selected_date_display", type=str)

    (cal, planned_days, approved_days,
     new_moon_days, phase1_moon_days, phase2_moon_days, phase3_moon_days,
     full_moon_days, phase5_moon_days, phase6_moon_days, phase7_moon_days) = calendar_service(year, month)
    today = date.today()
    referrer = request.referrer

    template = "_calendar.html" if request.headers.get("HX-Request") else "calendar.html"
    month_name = [ "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember" ]
    return render_template(
        template,
        datetime=datetime,
        cal=cal,
        planned_days=planned_days,
        approved_days=approved_days,
        full_moon_days=full_moon_days,
        phase1_moon_days=phase1_moon_days,
        phase2_moon_days=phase2_moon_days,
        phase3_moon_days=phase3_moon_days,
        new_moon_days=new_moon_days,
        phase5_moon_days=phase5_moon_days,
        phase6_moon_days=phase6_moon_days,
        phase7_moon_days=phase7_moon_days,
        month=month,
        year=year,
        today_day=today.day,
        today_month=today.month,
        today_year=today.year,
        referrer=referrer,
        picker=picker,
        target_id=target_id,
        display_id=display_id,
        month_name=month_name
    )
