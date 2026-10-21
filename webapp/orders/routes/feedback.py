from datetime import date, datetime, timezone

from flask import (
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import select

from webapp import db
from webapp.model.db import Observatory, Telescope, Filterset
from webapp.model.feedback import (
    ObservationFeedback,
    ObservationFeedbackPosition,
)
from webapp.orders import orders
from webapp.orders.constants import (
    ORDER_STATUS_STATISTICS_OPEN,
    ORDER_STATUS_DOCUMENTED,
)
from webapp.orders.feedbackform import FeedbackForm
from webapp.orders.feedbackservice import POSITION_COLUMNS
from webapp.users.utils import role_required


EDIT_HEAD = (
    'name',
    'request_date',
    'request_observatory_id',
    'remark',
)

EDIT_POSITION = tuple(
    name
    for name in POSITION_COLUMNS
    if name not in ('observation_request_id', 'row_no')
)


def feedback_values(feedback):
    values = {
        name: getattr(feedback, name)
        for name in EDIT_HEAD
    }

    values['positions'] = []

    for position in feedback.positions:
        row_values = {}

        for name in EDIT_POSITION:
            value = getattr(position, name)

            if value is None:
                if name == 'filterset_id':
                    value = 0
                elif name in (
                    'dec_sign',
                    'target_coordinates_lock',
                ):
                    value = ''

            row_values[name] = value

        values['positions'].append(row_values)

    return values

def build_feedback_form(feedback):
    form = FeedbackForm(data=feedback_values(feedback))

    form.request_observatory_id.choices = [
        (observatory.id, observatory.name)
        for observatory in Observatory.query.order_by(
            Observatory.name
        ).all()
    ]

    telescopes = {
        telescope.id: telescope
        for telescope in Telescope.query.order_by(
            Telescope.name
        ).all()
    }

    filters = {
        filterset.id: filterset
        for filterset in Filterset.query.order_by(
            Filterset.priority
        ).all()
    }

    if (
        request.method == 'POST'
        and request.form.get('action') == 'add_position'
    ):
        if len(form.positions) >= 500:
            abort(400)

        form.positions.append_entry({
            'exposure_count': 1,
            'exposure_time': 1,
            'filterset_id': 0,
            'block_no': 1,
            'row_in_block': len(form.positions) + 1,
        })

    for row in form.positions:
        row.telescope_id.choices = [
            (telescope.id, telescope.name)
            for telescope in telescopes.values()
        ]

        row.filterset_id.choices = [
            (0, 'Kein Filterset')
        ] + [
            (filterset.id, filterset.name)
            for filterset in filters.values()
        ]

    return form, telescopes, filters

def validate_feedback_changes(form, telescopes, filters):
    valid = True

    if not (form.deviations.data or '').strip():
        form.deviations.errors.append(
            'Bitte die Abweichungen beschreiben.'
        )
        valid = False

    if form.request_date.data > date.today():
        form.request_date.errors.append(
            'Das Beobachtungsdatum darf nicht '
            'in der Zukunft liegen.'
        )
        valid = False

    if not form.positions:
        form.confirm.errors.append(
            'Bitte mindestens eine Aufnahmezeile angeben.'
        )
        valid = False

    for row in form.positions:
        telescope = telescopes[row.telescope_id.data]
        filterset = filters.get(row.filterset_id.data)

        if (
            telescope.observatory_id
            != form.request_observatory_id.data
        ):
            row.telescope_id.errors.append(
                'Das Teleskop gehört nicht '
                'zum ausgewählten Observatorium.'
            )
            valid = False

        if (
            filterset
            and filterset.telescope_id != telescope.id
        ):
            row.filterset_id.errors.append(
                'Das Filterset gehört nicht '
                'zum ausgewählten Teleskop.'
            )
            valid = False

    return valid

def save_feedback(feedback, form):
    changed = form.matches_request.data == 'no'

    if changed:
        for name in EDIT_HEAD:
            value = getattr(form, name).data

            if name == 'request_date':
                value = datetime.combine(
                    value,
                    datetime.min.time(),
                )

            setattr(feedback, name, value)

        for index, row in enumerate(form.positions):
            if index < len(feedback.positions):
                position = feedback.positions[index]
            else:
                position = ObservationFeedbackPosition(
                    observation_request_id=feedback.source_request_id,
                    row_no=index + 1,
                )

                feedback.positions.append(position)

            for name in EDIT_POSITION:
                value = getattr(row, name).data

                if name in (
                    'filterset_id',
                    'dec_sign',
                    'target_coordinates_lock',
                ):
                    value = value or None

                setattr(position, name, value)

        if len(form.positions) < len(feedback.positions):
            del feedback.positions[len(form.positions):]

        feedback.deviations = form.deviations.data

    feedback.matches_request = not changed
    feedback.status = ORDER_STATUS_DOCUMENTED
    feedback.completed_at = datetime.now(timezone.utc)
    feedback.completed_by_id = current_user.id

    db.session.commit()

@orders.route(
    '/feedback/<int:feedback_id>',
    methods=['GET', 'POST'],
)

@login_required
@role_required('user')
def observation_feedback(feedback_id):
    statement = select(ObservationFeedback).where(
        ObservationFeedback.id == feedback_id
    )

    if request.method == 'POST':
        statement = statement.with_for_update()

    feedback = db.session.execute(
        statement
    ).scalar_one_or_none()

    if feedback is None:
        abort(404)

    if feedback.user_id != current_user.id:
        abort(403)

    if feedback.status != ORDER_STATUS_STATISTICS_OPEN:
        abort(
            409,
            description='Diese Rückmeldung ist bereits abgeschlossen.',
        )

    form, telescopes, filters = build_feedback_form(feedback)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'complete':
            if form.validate_on_submit():
                changed = form.matches_request.data == 'no'

                valid = (
                    validate_feedback_changes(
                        form,
                        telescopes,
                        filters,
                    )
                    if changed
                    else True
                )

                if valid:
                    save_feedback(feedback, form)

                    flash(
                        'Die Beobachtungsrückmeldung wurde '
                        'abgeschlossen und gespeichert.',
                        'success',
                    )

                    return redirect(
                        url_for('orders.show_orders')
                    )

        elif action != 'add_position':
            abort(400)

    return render_template(
        'observation_feedback.html',
        title='Beobachtungsrückmeldung',
        feedback=feedback,
        form=form,
    )