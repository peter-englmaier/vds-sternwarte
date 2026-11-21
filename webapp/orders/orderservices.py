from flask_login import current_user
from datetime import datetime, timedelta, time
import uuid
from webapp.model.db import Catalogue
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
import re
from webapp import db
from .constants import ORDER_STATUS_CREATED, ORDER_STATUS_WAITING, USER_ROLE_ADMIN
from webapp.model.db import UserPreferences, ObservatoryReservation, Observatory
from webapp.model.db import User
from .orderform import telescope_query, filterset_query

# --------------------------------------------------------------------------
#  Umformung von dezimal Koordinaten in die Stunden / Minuten und Winkelgrad
# --------------------------------------------------------------------------
def deg_to_hms(ra_deg):
    hours = ra_deg / 15
    h = int(hours)
    m = int((hours - h) * 60)
    s = (hours - h - m/60) * 3600
    return f"{h:02d}:{m:02d}:{s:06.3f}"

def deg_to_dms(dec_deg):
    sign = '+' if dec_deg >= 0 else '-'
    dec_deg = abs(dec_deg)
    d = int(dec_deg)
    m = int((dec_deg - d) * 60)
    s = (dec_deg - d - m/60) * 3600
    return f"{sign}{d:02d}:{m:02d}:{s:05.2f}"

# --------------------------------------------------------------------------
# Neuen Antrags-Positionssarz mit Defaultwerten initialisieren
# Angenomme Defaultwerte. Könnte man auch aus Template Datensätzen holen
# --------------------------------------------------------------------------
def init_new_orderpos_service():
    pos = ObservationRequestPosition()
    pos.telescope_id = -1
    pos.filterset_id = -1
    pos.target = ''
    pos.target_objecttype = ''
    pos.target_coordinates = ''
    pos.target_coordinates_lock = '0'
    pos.exposure_count = 20
    pos.exposure_time = 300
    pos.exposure_starttime = None
    pos.exposure_gain = 10
    pos.exposure_offset = 0
    pos.exposure_dither = 1
    pos.exposure_focus = 0
    return [pos]

# --------------------------------------------------------------------------
# Kopieren eines Antrags
# --------------------------------------------------------------------------
def copy_order_service(order_id):
    orig_order = ObservationRequest.query.get_or_404(order_id)
    try:
        new_order = ObservationRequest()
        for column in ObservationRequest.__table__.columns:
            setattr(
                new_order,
                column.name,
                getattr(orig_order, column.name),
            )

        new_order.id = None
        new_order.user_id = current_user.id
        new_order.name = orig_order.name
        new_order.status = ORDER_STATUS_CREATED
        new_order.date_created = datetime.now()

        db.session.add(new_order)
        db.session.flush()

        orig_positions = (
            ObservationRequestPosition.query
            .filter_by(observation_request_id=order_id)
            .order_by(ObservationRequestPosition.row_no)
            .all()
        )

        for pos in orig_positions:
            position_new = ObservationRequestPosition()
            for column in ObservationRequestPosition.__table__.columns:
                setattr(
                    position_new,
                    column.name,
                    getattr(pos, column.name),
                )

            position_new.id = None
            position_new.observation_request_id = new_order.id
            db.session.add(position_new)

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return 1, f'Es ist ein Fehler aufgetreten:\n{e}.\nBitte melden Sie sich beim Systemadministrator.'
    return 0, "Antrag \nerfolgreich\n kopiert."


# --------------------------------------------------------------------------
# Löschen eines Antrags
# --------------------------------------------------------------------------

def delete_order_service(order_id):
    order = ObservationRequest.query.get_or_404(order_id)
    reservation=ObservatoryReservation.query.filter_by(observation_request_id=order_id).first()
    try:
        if reservation:
            db.session.delete(reservation)
            db.session.commit()
        db.session.delete(order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return 1, f'Es ist ein Fehler aufgetreten:\n{e}.\nBitte melden Sie sich beim Systemadministrator.'
    return 0, "Antrag \nerfolgreich\n gelöscht."

# --------------------------------------------------------------------------
# Suche nach Objekt in Katalogen, Rückgabe des gefundenen Datensatzes
# --------------------------------------------------------------------------

def catalogue_query(sky_object):
    norm_name = re.sub(r'[\W]', '', sky_object, flags=re.UNICODE).upper()
    return (
        Catalogue.query
        .filter(
            func.replace(
                func.replace(
                    func.replace(func.upper(Catalogue.name), '-', ''),
                    ' ',
                    ''
                ),
                '.',
                ''
            ) == norm_name
        )
        .first()
    )

# ------------------------------------------------------------------------------------------------------
# Ergänzung der zu einer Liste von Objekten gehörenden Koordinaten, Rückgabe in Stunden, Minuten und so
# ------------------------------------------------------------------------------------------------------
#from astropy.coordinates import SkyCoord
#from astropy import units as u

def resolve_coordinates_service( orderpositions ):
    count = len(orderpositions)
    resolved = 0
    ambigious = 0
    for item in orderpositions:
        if not item.target_coordinates_lock.data :
            norm_object  = re.sub(r'[^\w]', '', item.target.data, flags=re.UNICODE).upper()
            coordinates = catalogue_query(norm_object)
            if coordinates:
# Mit Astropy
#                item.target_coordinates.data = SkyCoord(ra=coordinates.ra * u.degree, dec=coordinates.dec * u.degree)
                item.target_coordinates.data = deg_to_hms(coordinates.ra) + ' ' + deg_to_dms(coordinates.dec)
                resolved += 1
            else:
                ambigious += 1
                item.target_coordinates.data = '???'

    return orderpositions, count, resolved, ambigious

import calendar
from webapp.model.db import ObservationRequest, ObservationRequestPosition

# ------------------------------------------------------------------
# User preference laden  ( könnte besser ins User Modul )
# ------------------------------------------------------------------
def get_user_preference_service(user_id, key, default=None):
    if not key:
        raise ValueError("Parameter 'key' is required")
    pref = UserPreferences.query.filter_by(user_id=user_id, key=key).first()
    return pref.value if pref else default

# ------------------------------------------------------------------
# User preference speichern
# ------------------------------------------------------------------

def set_user_preference_service( user_id, key, value, default=None ):
    if not key:
        raise ValueError("Parameter 'key' is required")
    pref = UserPreferences.query.filter_by(user_id=user_id, key=key).first()
    if not pref:
        pref = UserPreferences(user_id=current_user.id, key=key)
        db.session.add(pref)
    pref.value = str(value)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return 1, f'Es ist ein Fehler aufgetreten:\n{e}.\nBitte melden Sie sich beim Systemadministrator.'
    return 0, None


# ----------------------------------------------------------------------------
#  Mondphasenberechnung
# ----------------------------------------------------------------------------

def moon_phases(year, month):
    # Referenz-Neumond: 25. Juni 2025, 12:31 UTC
    ref_new_moon = datetime(2025, 6, 25, 12, 31)
    synodic_month = 29.53059  # mittlere synodische Periode in Tagen

    # Start und Ende des Monats
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Suche nach Neumond und Vollmond im gewünschten Monat
    new_moon_days = set()    # mond unbeleuchtet
    phase1_moon_days = set() # mond 25% beleuchtet
    phase2_moon_days = set() # mond 50% beleuchtet
    phase3_moon_days = set() # mond 75% beleuchtet
    full_moon_days = set() # mond 100% beleuchtet
    phase5_moon_days = set() # mond 75% beleuchtet
    phase6_moon_days = set() # mond 50% beleuchtet
    phase7_moon_days = set() # mond 25% beleuchtet

    # Wir durchsuchen einen Zeitraum von 2 Monaten um den Zielmonat herum
    days_before = 30
    search_start = start_date - timedelta(days=days_before)
    search_end = end_date + timedelta(days=days_before)

    # Berechne die Zahl k für den nächsten Neumond nach Referenz
    k = int((search_start - ref_new_moon).days / synodic_month)
    while True:
        # Zeitpunkt des k-ten Neumonds
        new_moon = ref_new_moon + timedelta(days=k * synodic_month)
        if new_moon > search_end:
            break
        # Neumond im Zielmonat?
        if new_moon.year == year and new_moon.month == month:
            new_moon_days.add(new_moon.day)
        # 1/4 Mond
        phase1_moon = new_moon + timedelta(days=synodic_month * 1 / 8)
        if phase1_moon.year == year and phase1_moon.month == month:
            phase1_moon_days.add(phase1_moon.day)
        # 1/2 Mond
        phase2_moon = new_moon + timedelta(days=synodic_month * 2 / 8)
        if phase2_moon.year == year and phase2_moon.month == month:
            phase2_moon_days.add(phase2_moon.day)
        # 3/4 Mond
        phase3_moon = new_moon + timedelta(days=synodic_month * 3 / 8)
        if phase3_moon.year == year and phase3_moon.month == month:
            phase3_moon_days.add(phase3_moon.day)
        # full moon
        full_moon = new_moon + timedelta(days=synodic_month / 2)
        if full_moon.year == year and full_moon.month == month:
            full_moon_days.add(full_moon.day)
        # 3/4 Mond (abnehmend)
        phase5_moon = new_moon + timedelta(days=synodic_month * 5 / 8)
        if phase5_moon.year == year and phase5_moon.month == month:
            phase5_moon_days.add(phase5_moon.day)
        # 1/2 Mond (abnehmend)
        phase6_moon = new_moon + timedelta(days=synodic_month * 6 / 8)
        if phase6_moon.year == year and phase6_moon.month == month:
            phase6_moon_days.add(phase6_moon.day)
        # 1/4 Mond (abnehmend)
        phase7_moon = new_moon + timedelta(days=synodic_month * 7 / 8)
        if phase7_moon.year == year and phase7_moon.month == month:
            phase7_moon_days.add(phase7_moon.day)

        k += 1

    return (new_moon_days, phase1_moon_days, phase2_moon_days, phase3_moon_days,
            full_moon_days, phase5_moon_days, phase6_moon_days, phase7_moon_days)

# ------------------------------------------------------------------------------------------------------
# Kalender, der die gebuchten und in Planung befindlichen Tage sowohl Voll- und Neumond Tage in einem
# vorgegebenen Monat darstellt.
# ------------------------------------------------------------------------------------------------------

def calendar_service(year, month):
    reservations = ObservatoryReservation.query.filter(
        db.extract('year', ObservatoryReservation.date) == year,
        db.extract('month', ObservatoryReservation.date) == month,
    ).all()
    approved_days = set()
    planned_days = set()
    # gebuchte Tage
    for request in reservations:
        if request.is_booked() or request.is_frozen():
            approved_days.add(request.date.day)
        elif not request.is_expired():
            planned_days.add(request.date.day)

    # hier einfach ausgerechnet. Besser mit astropy?
    (new_moon_days, phase1_moon_days, phase2_moon_days, phase3_moon_days,
     full_moon_days, phase5_moon_days, phase6_moon_days, phase7_moon_days) = moon_phases(year, month)

    cal = calendar.monthcalendar(year, month)
    return (cal, planned_days, approved_days,
            new_moon_days, phase1_moon_days, phase2_moon_days, phase3_moon_days,
            full_moon_days, phase5_moon_days, phase6_moon_days, phase7_moon_days)



# --------------------------------------------------------------------------
# Antragskopf und Positionen aus dem Formular übernehmen.
# Gemeinsam genutzt von create_order.actionhandler (neuer Antrag) und
# edit_order_pos.edit_order_pos (bestehender Antrag).
# --------------------------------------------------------------------------
def default_positions(observatory_id):
    """Return a list with one default position matching the observatory.

    :param observatory_id: id of the observatory, may be ``None``.
    :return: list with one unsaved ``ObservationRequestPosition`` that uses
        the first telescope and filter set of the observatory.
    """
    position_items = init_new_orderpos_service()
    telescopes = telescope_query(observatory_id)
    if telescopes:
        position_items[0].telescope_id = telescopes[0].id
        filtersets = filterset_query(telescopes[0].id)
        if filtersets:
            position_items[0].filterset_id = filtersets[0].id
    position_items[0].block_no = 1
    position_items[0].row_in_block = 1
    return position_items


def position_data(position_items):
    """Convert positions into the data dicts of ``form.positions``.

    :param position_items: iterable of ``ObservationRequestPosition``.
    :return: list of dicts for ``form.process(data={"positions": ...})``.
    """
    return [
        {
            "telescope": pos.telescope_id,
            "target": pos.target,
            "filterset": pos.filterset_id,
            "target_objecttype": pos.target_objecttype,
            "target_coordinates": pos.target_coordinates,
            "target_coordinates_lock": pos.target_coordinates_lock != "0",
            "exposure_count": pos.exposure_count,
            "exposure_time": pos.exposure_time,
            "mosaic": bool(getattr(pos, "mosaic", False)),
            "exposure_starttime": pos.exposure_starttime,
            "exposure_gain": pos.exposure_gain,
            "exposure_offset": pos.exposure_offset,
            "exposure_dither": pos.exposure_dither,
            "exposure_focus": pos.exposure_focus,
        }
        for pos in position_items
    ]


def group_blocks(block_numbers):
    """Build the block structure the template ``edit_order_pos.html`` expects.

    :param block_numbers: block number of each position, in form order.
    :return: ``[{"block_no": int, "row_indices": [...]}, ...]``; the row
        indices refer to the global list ``form.positions``.
    """
    blocks = []
    current_block = None
    for global_idx, bno in enumerate(block_numbers):
        if current_block is None or current_block["block_no"] != bno:
            current_block = {"block_no": bno, "row_indices": []}
            blocks.append(current_block)
        current_block["row_indices"].append(global_idx)
    return blocks


def _posted_int(form_data, key):
    """Read an integer from posted form data, ``1`` if missing or invalid."""
    try:
        return int(form_data.get(key, "1"))
    except ValueError:
        return 1


def posted_block_numbers(form_data, count):
    """Read the block numbers of the posted positions.

    The values come from the hidden inputs ``positions-<idx>-block_no`` that
    the flattening javascript of ``edit_order_pos.html`` creates.

    :param form_data: posted form data, usually ``request.form``.
    :param count: number of positions in the form.
    :return: list of ``count`` block numbers; ``1`` for missing values.
    """
    return [_posted_int(form_data, f"positions-{idx}-block_no") for idx in range(count)]


def set_position_choices(form, observatory_id):
    """Set the telescope and filter set choices of all positions.

    :param form: ``ObservationRequestPositionsForm`` with its positions.
    :param observatory_id: id of the observatory whose telescopes are offered.
    """
    tel_choices = [(x.id, x.name) for x in telescope_query(observatory_id)]
    for pos_form in form.positions:
        pos_form.telescope.choices = tel_choices
        selected_telescope_id = pos_form.telescope.data
        fs_choices = filterset_query(selected_telescope_id) if selected_telescope_id else []
        if not pos_form.filterset.data:
            pos_form.filterset.choices = [("", "Auswählen")] + [(x.id, x.name) for x in fs_choices]
        else:
            pos_form.filterset.choices = [(x.id, x.name) for x in fs_choices]


def apply_head(order_head, head_form):
    """Copy the editable head fields from the form into the order.

    Sets date, observatory, desired power user, type and remark. The
    requester name and the reservation are left to the caller.

    :param order_head: ``ObservationRequest`` to update (not committed).
    :param head_form: the ``head`` subform of ``ObservationRequestPositionsForm``.
    """
    order_head.request_date = head_form.request_date.data
    order_head.request_observatory_id = head_form.observatory_name.data
    poweruser_index = head_form.poweruser_name.data
    if poweruser_index:
        poweruser = next((name for i, name in head_form.poweruser_name.choices if i == poweruser_index), None)
        # poweruser now holds the display_name, not the name of the power user
        for pwuser in User.by_role('poweruser'):
            if pwuser.display_name() == poweruser:
                order_head.request_poweruser_id = pwuser.id
                break
    order_head.request_type = head_form.request_type.data
    order_head.remark = head_form.remark.data


def save_positions_service(form, order_id, form_data):
    """Replace the positions of an order with the posted ones.

    Adds the new positions to the session but does not commit.

    :param form: ``ObservationRequestPositionsForm`` with the posted positions.
    :param order_id: id of the order the positions belong to.
    :param form_data: posted form data, usually ``request.form``; provides
        ``block_no`` and ``row_in_block`` of each position.
    """
    ObservationRequestPosition.query.filter_by(observation_request_id=order_id).delete()

    block_numbers = posted_block_numbers(form_data, len(form.positions))
    for idx, pos_form in enumerate(form.positions):
        row_in_block = _posted_int(form_data, f"positions-{idx}-row_in_block")

        # target_coordinates_lock: DB ist VARCHAR(1)
        # -> konsistent als "0"/"1" speichern, damit GET ( != "0") stimmt
        lock_val = pos_form.target_coordinates_lock.data
        if isinstance(lock_val, str):
            lock_db = lock_val
        else:
            lock_db = "1" if lock_val else "0"

        db.session.add(
            ObservationRequestPosition(
                row_no=idx + 1,
                block_no=block_numbers[idx],
                row_in_block=row_in_block,
                observation_request_id=order_id,
                telescope_id=pos_form.telescope.data,
                target=pos_form.target.data,
                filterset_id=pos_form.filterset.data,
                target_objecttype=pos_form.target_objecttype.data,
                target_coordinates=pos_form.target_coordinates.data,
                target_coordinates_lock=lock_db,
                exposure_count=pos_form.exposure_count.data,
                exposure_time=pos_form.exposure_time.data,
                mosaic=bool(pos_form.mosaic.data),
                exposure_starttime=pos_form.exposure_starttime.data,
                exposure_gain=pos_form.exposure_gain.data,
                exposure_offset=pos_form.exposure_offset.data,
                exposure_dither=pos_form.exposure_dither.data,
                exposure_focus=pos_form.exposure_focus.data,
            )
        )


def submit_order_service(order_id):
    """Submit an order for approval and freeze its reservation.

    :param order_id: id of the order to submit.
    :return: list of ``(message, category)`` tuples for ``flash()``; empty
        if everything worked.
    """
    messages = []
    order_head = ObservationRequest.query.get(order_id)
    order_head.status = ORDER_STATUS_WAITING
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        messages.append((
            f"Es ist ein Fehler aufgetreten: {e}. Bitte melden Sie sich beim Systemadministrator.",
            "danger",
        ))

    reservation = ObservatoryReservation.query.filter_by(observation_request_id=order_id).first()
    if reservation:
        try:
            reservation.freeze()
            db.session.add(reservation)
            db.session.commit()
        except Exception:
            db.session.rollback()
            messages.append((
                "Die Reservierung ist bereits abgelaufen und kann nicht mehr aufrechterhalten werden.",
                "warning",
            ))
    return messages


def order_form_problems(form):
    """Check the posted order form for data the database needs.

    The form is not validated with WTForms, so missing values would only show
    up as database errors when saving.

    :param form: ``ObservationRequestPositionsForm`` with the posted data.
    :return: list of messages for the user; empty if the order can be saved.
    """
    problems = []
    if not form.head.request_date.data:
        problems.append("Bitte wähle über den Button „Kalender“ ein Datum aus.")
    if not form.head.observatory_name.data:
        problems.append("Bitte wähle ein Observatorium aus.")
    if any(not pos_form.telescope.data for pos_form in form.positions):
        problems.append("Bitte wähle in jeder Aufnahmezeile ein Teleskop aus.")
    return problems


DATE_TAKEN_MESSAGE = "Der {date} ist bereits reserviert. Bitte wähle ein anderes Datum."
SAVE_FAILED_MESSAGE = (
    "{what} konnte nicht gespeichert werden (Fehler-Referenz {reference}). "
    "Bitte versuche es erneut oder wende dich mit dieser Referenz an den Administrator."
)


def error_reference():
    """Return a short id that links a message for the user to its log entry.

    :return: 8 hex characters, e.g. ``"3f9a1c0b"``.
    """
    return uuid.uuid4().hex[:8]


def save_failed_message(what, reference):
    """Build the message shown when saving failed for an unexpected reason.

    :param what: what could not be saved, e.g. ``"Der Antrag"``.
    :param reference: value of :func:`error_reference`, also written to the log.
    :return: message for ``flash()``.
    """
    return SAVE_FAILED_MESSAGE.format(what=what, reference=reference)


def reservation_error_message(exc, requested_date, reference):
    """Explain why committing a reservation failed.

    :param exc: the exception raised by ``db.session.commit()``.
    :param requested_date: the requested date (``date`` or ``datetime``).
    :param reference: value of :func:`error_reference`, also written to the log.
    :return: message for ``flash()``; names the date if it is already taken.
    """
    if isinstance(exc, IntegrityError) and "observatory_reservation.date" in str(exc.orig):
        return DATE_TAKEN_MESSAGE.format(date=requested_date.strftime('%d.%m.%Y'))
    return save_failed_message("Die Reservierung", reference)


def prepare_reservation_service(order_head):
    """Create or update the reservation of an order for its requested date.

    Each date can be reserved only once (``observatory_reservation.date`` is
    unique). A reservation of another order for the same date blocks it as
    long as it is valid; an expired one is deleted, because the calendar
    already shows its date as free.

    Adds the reservation to the session but does not commit.

    :param order_head: ``ObservationRequest`` with ``id``, ``request_date``
        and ``request_observatory_id`` set.
    :return: ``(reservation, message)``; ``reservation`` is ``None`` and
        ``message`` explains why if the date cannot be reserved.
    """
    observatory = Observatory.query.get(order_head.request_observatory_id) \
        if order_head.request_observatory_id else None
    if not order_head.request_date or observatory is None:
        return None, "Bitte wähle Datum und Observatorium aus."

    reservation_date = ObservatoryReservation.date_sanitize(order_head.request_date)
    # The column is stored as "YYYY-MM-DD 00:00:00.000000"; compare with a
    # datetime, a plain date would be compared as "YYYY-MM-DD" and never match.
    day = reservation_date.date() if isinstance(reservation_date, datetime) else reservation_date
    other = ObservatoryReservation.query.filter(
        ObservatoryReservation.date == datetime.combine(day, time.min),
        ObservatoryReservation.observation_request_id != order_head.id,
    ).first()
    if other is not None:
        if not other.is_expired():
            return None, DATE_TAKEN_MESSAGE.format(date=day.strftime('%d.%m.%Y'))
        db.session.delete(other)
        db.session.flush()  # free the unique date before the new row is written

    reservation = ObservatoryReservation.query.filter_by(observation_request_id=order_head.id).first()
    if reservation is None:
        reservation = ObservatoryReservation(reservation_date, observatory, order_head)
    else:
        reservation.set_observatory(observatory).set_date(reservation_date)
    db.session.add(reservation)
    return reservation, None


def can_edit_order(order, user):
    """Tell whether a user may edit an order.

    Only the requester (or an admin) may edit, and only while the order is a
    draft. A rejected order stays as it is; it can be copied into a new draft.

    :param order: ``ObservationRequest`` to check.
    :param user: the user, usually ``current_user``.
    :return: ``True`` if the user may open the edit page of the order.
    """
    if order.user_id != user.id and not user.has_role(USER_ROLE_ADMIN):
        return False
    return order.status == ORDER_STATUS_CREATED
