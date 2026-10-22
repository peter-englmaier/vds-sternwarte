from flask_wtf import FlaskForm
from wtforms import (
    Form,
    StringField,
    TextAreaField,
    SelectField,
    BooleanField,
    IntegerField,
    FloatField,
    DateField,
    TimeField,
    FieldList,
    FormField,
)
from wtforms.validators import (
    InputRequired,
    Optional,
    Length,
    NumberRange,
)

# Formulare und Eingabeprüfungen für Beobachtungsrückmeldungen.
# Eingabefelder einer Aufnahmezeile.

class FeedbackPositionForm(Form):
    telescope_id = SelectField(
        'Teleskop', coerce=int, validators=[InputRequired()]
    )

    filterset_id = SelectField('Filterset', coerce=int)

    target = StringField(
        'Objekt', validators=[InputRequired(), Length(max=200)]
    )

    target_objecttype = StringField(
        'Objekttyp', validators=[Optional(), Length(max=200)]
    )

    target_coordinates = StringField(
        'Koordinaten', validators=[Optional(), Length(max=200)]
    )

    target_coordinates_lock = SelectField(
        'Koordinaten gesperrt',
        choices=[('', 'Keine Angabe'), ('0', 'Nein'), ('1', 'Ja')],
    )

    exposure_count = IntegerField(
        'Anzahl Bilder',
        validators=[InputRequired(), NumberRange(min=0)],
    )

    exposure_time = IntegerField(
        'Belichtungszeit (s)',
        validators=[InputRequired(), NumberRange(min=1)],
    )

    mosaic = BooleanField('Mosaik')

    exposure_gain = IntegerField(
        'Gain', validators=[Optional(), NumberRange(min=0)]
    )

    exposure_offset = IntegerField(
        'Offset', validators=[Optional(), NumberRange(min=0)]
    )

    exposure_dither = IntegerField(
        'Dithern', validators=[Optional(), NumberRange(min=0)]
    )

    exposure_focus = IntegerField(
        'Fokussieren', validators=[Optional(), NumberRange(min=0)]
    )

    exposure_starttime = TimeField(
        'Startzeit', validators=[Optional()]
    )

    ra_h = IntegerField(
        'RA Stunden',
        validators=[Optional(), NumberRange(min=0, max=23)],
    )

    ra_m = IntegerField(
        'RA Minuten',
        validators=[Optional(), NumberRange(min=0, max=59)],
    )

    ra_s = FloatField(
        'RA Sekunden',
        validators=[Optional(), NumberRange(min=0, max=59.999999)],
    )

    dec_sign = SelectField(
        'DEC Vorzeichen',
        choices=[('', 'Keine Angabe'), ('+', '+'), ('-', '-')],
    )

    dec_d = IntegerField(
        'DEC Grad',
        validators=[Optional(), NumberRange(min=0, max=90)],
    )

    dec_m = IntegerField(
        'DEC Minuten',
        validators=[Optional(), NumberRange(min=0, max=59)],
    )

    dec_s = FloatField(
        'DEC Sekunden',
        validators=[Optional(), NumberRange(min=0, max=59.999999)],
    )

    block_no = IntegerField(
        'Block', validators=[InputRequired(), NumberRange(min=1)]
    )

    row_in_block = IntegerField(
        'Zeile im Block',
        validators=[InputRequired(), NumberRange(min=1)],
    )


class FeedbackForm(FlaskForm):
    matches_request = SelectField(
        'Durchführung gemäß Antrag?',
        choices=[
            ('', 'Bitte auswählen'),
            ('yes', 'Ja, gemäß Antrag'),
            ('no', 'Nein, mit Abweichungen'),
        ],
    )

    name = StringField(
        'Beteiligte',
        validators=[InputRequired(), Length(max=100)],
    )

    request_date = DateField(
        'Tatsächliches Datum',
        validators=[InputRequired()],
    )

    request_observatory_id = SelectField(
        'Observatorium',
        coerce=int,
        validators=[InputRequired()],
    )

    remark = TextAreaField(
        'Anmerkungen',
        validators=[Optional(), Length(max=2000)],
    )

    deviations = TextAreaField(
        'Abweichungen',
        validators=[Optional(), Length(max=2000)],
    )

    positions = FieldList(
        FormField(FeedbackPositionForm),
        max_entries=500,
    )

    confirm = BooleanField(
        'Ich bestätige die Richtigkeit der Beobachtungsdaten.',
        validators=[InputRequired()],
    )

    def validate(self, extra_validators=None):
        # Das Bearbeitungsformular übermittelt keine Auswahl mehr.
        # In diesem Fall werden die Aufnahmezeilen geprüft und gespeichert.
        if self.matches_request.data in (None, ''):
            self.matches_request.data = 'no'

        names = ['matches_request', 'confirm']

        if 'csrf_token' in self._fields:
            names.append('csrf_token')

        # Der grüne Daumen bestätigt unverändert.
        # Beim Bearbeiten müssen auch die Aufnahmezeilen gültig sein.
        if self.matches_request.data != 'yes':
            names.append('positions')

        results = [
            self._fields[name].validate(
                self,
                (extra_validators or {}).get(name, ()),
            )
            for name in names
        ]

        return all(results)