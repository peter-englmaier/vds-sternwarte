from flask import abort, render_template, request
from flask_login import login_required

from webapp.main import main
from webapp.model.db import User
from webapp.users.utils import role_required


@main.route('/observationlist_complete', methods=['GET'])
@login_required
@role_required("user")
def observation_database():
    from datetime import date, datetime
    from sqlalchemy import extract, or_
    from sqlalchemy.orm import contains_eager, selectinload

    from webapp.model.feedback import (
        ObservationFeedback,
        ObservationFeedbackPosition,
    )
    from webapp.model.db import Telescope, Filterset
    from webapp.orders.constants import ORDER_STATUS_DOCUMENTED

    search = request.args.get('q', '').strip()

    base_query = ObservationFeedback.query.filter(
        ObservationFeedback.status == ORDER_STATUS_DOCUMENTED,
        ObservationFeedback.completed_at.isnot(None),
    )

    month_rows = (
        base_query
        .with_entities(
            extract('year', ObservationFeedback.request_date).label('year'),
            extract('month', ObservationFeedback.request_date).label('month'),
        )
        .distinct()
        .all()
    )

    available_months = sorted(
        {(int(row.year), int(row.month)) for row in month_rows},
        reverse=True,
    )

    default_year, default_month = (
        available_months[0]
        if available_months
        else (date.today().year, date.today().month)
    )

    # Bei einer Suche gelten keine Jahres- oder Monatsfilter.
    if search:
        selected_year = default_year
        selected_month = default_month
    else:
        try:
            selected_year = int(request.args.get('year', default_year))
            selected_month = int(request.args.get('month', default_month))
        except (TypeError, ValueError):
            abort(400, description='Jahr und Monat müssen Zahlen sein.')

        if not 1 <= selected_year <= 9998:
            abort(400, description='Ungültiges Jahr.')

        if not 1 <= selected_month <= 12:
            abort(400, description='Ungültiger Monat.')

    month_names = (
        'Januar', 'Februar', 'März', 'April',
        'Mai', 'Juni', 'Juli', 'August',
        'September', 'Oktober', 'November', 'Dezember',
    )

    month_choices = list(enumerate(month_names, start=1))

    year_choices = sorted(
        {year for year, month in available_months} | {selected_year},
        reverse=True,
    )

    older_month = None
    newer_month = None

    if search:
        # Sonderzeichen als Suchtext behandeln.
        escaped_search = (
            search
            .replace('\\', '\\\\')
            .replace('%', '\\%')
            .replace('_', '\\_')
        )
        pattern = f'%{escaped_search}%'

        # Nur passende Aufnahmezeilen laden.
        feedbacks = (
            base_query
            .join(ObservationFeedback.positions)
            .filter(
                or_(
                    ObservationFeedbackPosition.target.ilike(
                        pattern, escape='\\'
                    ),
                    ObservationFeedbackPosition.target_objecttype.ilike(
                        pattern, escape='\\'
                    ),
                )
            )
            .options(
                contains_eager(ObservationFeedback.positions),
                selectinload(ObservationFeedback.observatory_name),
            )
            .populate_existing()
            .order_by(
                ObservationFeedback.request_date.desc(),
                ObservationFeedback.id.desc(),
                ObservationFeedbackPosition.row_no.asc(),
            )
            .all()
        )

    else:
        month_start = datetime(selected_year, selected_month, 1)

        if selected_month == 12:
            next_month_start = datetime(selected_year + 1, 1, 1)
        else:
            next_month_start = datetime(
                selected_year,
                selected_month + 1,
                1,
            )

        feedbacks = (
            base_query
            .filter(
                ObservationFeedback.request_date >= month_start,
                ObservationFeedback.request_date < next_month_start,
            )
            .options(
                selectinload(ObservationFeedback.positions),
                selectinload(ObservationFeedback.observatory_name),
            )
            .order_by(
                ObservationFeedback.request_date.desc(),
                ObservationFeedback.id.desc(),
            )
            .all()
        )

        selected_period = (selected_year, selected_month)

        older_month = next(
            (
                period for period in available_months
                if period < selected_period
            ),
            None,
        )

        newer_month = next(
            (
                period for period in reversed(available_months)
                if period > selected_period
            ),
            None,
        )

    user_ids = set()
    telescope_ids = set()
    filterset_ids = set()

    for feedback in feedbacks:
        user_ids.add(feedback.user_id)

        if feedback.request_poweruser_id:
            user_ids.add(feedback.request_poweruser_id)

        for position in feedback.positions:
            telescope_ids.add(position.telescope_id)

            if position.filterset_id:
                filterset_ids.add(position.filterset_id)

    users = {
        user.id: user.display_name()
        for user in User.query.filter(User.id.in_(user_ids)).all()
    } if user_ids else {}

    telescopes = {
        telescope.id: telescope.name
        for telescope in Telescope.query.filter(
            Telescope.id.in_(telescope_ids)
        ).all()
    } if telescope_ids else {}

    filtersets = {
        filterset.id: filterset.name
        for filterset in Filterset.query.filter(
            Filterset.id.in_(filterset_ids)
        ).all()
    } if filterset_ids else {}

    result_count = sum(
        len(feedback.positions) for feedback in feedbacks
    )

    return render_template(
        'observation_database.html',
        title='Beobachtungsdatenbank',
        feedbacks=feedbacks,
        search=search,
        result_count=result_count,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_month_label=(
            f'{month_names[selected_month - 1]} {selected_year}'
        ),
        year_choices=year_choices,
        month_choices=month_choices,
        older_month=older_month,
        newer_month=newer_month,
        users=users,
        telescopes=telescopes,
        filtersets=filtersets,
    )