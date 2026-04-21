import json
from flask import Response, request, flash, redirect, url_for
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from webapp.inout import bp
from webapp import db
from webapp.model.db import User, UserPreferences, Group, Role, Post, Site, Observatory, Telescope, Filterset, Poweruser, ObservationRequest, ObservationRequestPosition, ObservationHistory, SystemParameters, SystemParametersHistory, MotivationTypes, ObjectTypes, ObservationRequestLog, CatalogueMeta, Catalogue, user_group, role_group
from datetime import datetime, date, time
from webapp.users.utils import role_required

models = {
    'role': Role,
    'group': Group,
    'user': User,
    'post': Post,
    'user_preferences': UserPreferences,
    'site': Site,
    'observatory': Observatory,
    'telescope': Telescope,
    'filterset': Filterset,
    'poweruser': Poweruser,
    'observation_request': ObservationRequest,
    'observation_request_position': ObservationRequestPosition,
    'observation_history': ObservationHistory,
    'system_parameters': SystemParameters,
    'system_parameters_history': SystemParametersHistory,
    'motivation_types': MotivationTypes,
    'object_types': ObjectTypes,
    'observation_request_log': ObservationRequestLog,
    'catalogue_meta': CatalogueMeta,
    'catalogue': Catalogue
}
"""
A dictionary mapping table names to their corresponding models.
"""
ordered_tables = list(models.keys())
"""
A list of table names in the correct order for import/export.
"""

def _import_association_table(data, table, model1, model2, col1, col2):
    """
    Imports data for an association table, resolving foreign key relationships.

    Args:
        data (dict): The imported data.
        table (db.Table): The association table.
        model1 (db.Model): The first model in the relationship.
        model2 (db.Model): The second model in the relationship.
        col1 (str): The name of the first foreign key column.
        col2 (str): The name of the second foreign key column.
    """
    if table.__tablename__ in data:
        for record in data[table.__tablename__]:
            old_id1 = record.get(col1)
            old_id2 = record.get(col2)

            name1 = next((m['name'] for m in data[model1.__tablename__] if m['id'] == old_id1), None)
            name2 = next((m['name'] for m in data[model2.__tablename__] if m['id'] == old_id2), None)

            if name1 and name2:
                current_m1 = model1.query.filter_by(name=name1).first()
                current_m2 = model2.query.filter_by(name=name2).first()

                if current_m1 and current_m2:
                    stmt = select(table).where(and_(table.c[col1] == getattr(current_m1, 'id'), table.c[col2] == getattr(current_m2, 'id')))
                    exists = db.session.execute(stmt).first()
                    if not exists:
                        db.session.execute(table.insert().values({col1: getattr(current_m1, 'id'), col2: getattr(current_m2, 'id')}))

@bp.route('/inout/export', methods=['POST'])
@role_required('admin')
def export_data():
    """
    Exports all data from the database to a JSON file.
    """
    data = {}

    for table_name in ordered_tables:
        if table_name in models:
            model = models[table_name]
            records = model.query.all()
            data[table_name] = [record_to_dict(record) for record in records]

    # Also export the association tables
    data['user_group'] = [{'user_id': row[0], 'group_id': row[1]} for row in db.session.query(user_group).all()]
    data['role_group'] = [{'role_id': row[0], 'group_id': row[1]} for row in db.session.query(role_group).all()]

    json_data = json.dumps(data, indent=4, default=str)

    return Response(
        json_data,
        mimetype='application/json',
        headers={'Content-Disposition': 'attachment;filename=database_export.json'}
    )

@bp.route('/inout/import', methods=['POST'])
@role_required('admin')
def import_data():
    """
    Imports data from a JSON file into the database.
    """
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('admin.index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('admin.index'))
    if file:
        data = json.load(file.stream)
        
        for table_name in ordered_tables:
            if table_name in data and table_name in models:
                print(f'Importing {table_name}')
                model = models[table_name]
                for record in data[table_name]:
                    print(f'\t{record}')
                    # Convert string dates back to datetime objects
                    for c in model.__table__.columns:
                        col_name = c.name
                        if col_name in record and isinstance(record[col_name], str):
                            if isinstance(c.type, db.DateTime):
                                try:
                                    record[col_name] = datetime.fromisoformat(record[col_name])
                                except (ValueError, TypeError):
                                    flash(f"Warning: Could not parse datetime string '{record[col_name]}' for {table_name}.{col_name}. Setting to None.", "warning")
                                    record[col_name] = None
                            elif isinstance(c.type, db.Time):
                                try:
                                    record[col_name] = time.fromisoformat(record[col_name])
                                except (ValueError, TypeError):
                                    flash(f"Warning: Could not parse time string '{record[col_name]}' for {table_name}.{col_name}. Setting to None.", "warning")
                                    record[col_name] = None
                            elif isinstance(c.type, db.Date):
                                try:
                                    record[col_name] = date.fromisoformat(record[col_name])
                                except (ValueError, TypeError):
                                    flash(f"Warning: Could not parse date string '{record[col_name]}' for {table_name}.{col_name}. Setting to None.", "warning")
                                    record[col_name] = None

                    pk_name = model.__mapper__.primary_key[0].name
                    # skip columns in input which do not exist
                    valid_columns = [c.name for c in model.__table__.columns]
                    valid_columns.remove(pk_name) # also remove primary key
                    filtered_record = {k: v for k, v in record.items() if k in valid_columns}
                    instance = model(**filtered_record)
                    try:
                            db.session.add(instance)
                            db.session.commit()
                            print(f'added: \t{instance}')
                    except IntegrityError:
                        db.session.rollback()
                        print(f'value already exists {instance}')
            else:
                print(f'Skipping {table_name} (unknown table)')


        # Now handle the association tables: only import, if mapping does not already exist.
        _import_association_table(data, user_group, User, Group, 'user_id', 'group_id')
        _import_association_table(data, role_group, Role, Group, 'role_id', 'group_id')

        db.session.commit()
        flash('Data imported successfully. Existing records were ignored.')
    return redirect(url_for('admin.index'))

def record_to_dict(record):
    """
    Converts a SQLAlchemy model instance to a dictionary.

    Args:
        record (db.Model): The model instance to convert.

    Returns:
        dict: A dictionary representation of the model instance.
    """
    return {c.name: getattr(record, c.name) for c in record.__table__.columns}