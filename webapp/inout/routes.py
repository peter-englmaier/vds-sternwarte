import json
from flask import Response, request, flash, redirect, url_for
from sqlalchemy import select, and_
from sqlalchemy.exc import IntegrityError
from webapp.inout import bp
from webapp import db
from webapp.model.db import User, UserPreferences, Group, Role, Post, Site, Observatory, Telescope, Filterset, Poweruser, ObservationRequest, ObservationRequestPosition, ObservationHistory, SystemParameters, SystemParametersHistory, MotivationTypes, ObjectTypes, ObservationRequestLog, CatalogueMeta, Catalogue, user_group, role_group
from datetime import datetime, date, time
from webapp.users.utils import role_required

@bp.route('/inout/export', methods=['POST'])
@role_required('admin')
def export_data():
    data = {}

    models = [User, UserPreferences, Group, Role, Post, Site, Observatory, Telescope,
              Filterset, Poweruser, ObservationRequest, ObservationRequestPosition,
              ObservationHistory, SystemParameters, SystemParametersHistory, MotivationTypes,
              ObjectTypes, ObservationRequestLog, CatalogueMeta, Catalogue]

    for model in models:
        table_name = model.__tablename__
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
        Import data into database, which has been exported from same version.
        This works in two cases only:
            Case 1: some record has been deleted and needs to be restored. Note, that this will only work if
            no additional data has been added in the meantime.
            Case 2: the backend database has been replaced and data needs to be imported in the new database.
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
        
        models = {
            'user': User, 'user_preferences': UserPreferences, 'group': Group, 'role': Role, 'post': Post, 'site': Site,
            'observatory': Observatory, 'telescope': Telescope, 'filterset': Filterset, 'poweruser': Poweruser,
            'observation_request': ObservationRequest, 'observation_request_position': ObservationRequestPosition,
            'ObservationHistory': ObservationHistory, 'system_parameters': SystemParameters,
            'system_parameters_history': SystemParametersHistory, 'motivation_types': MotivationTypes,
            'object_types': ObjectTypes, 'observation_request_log': ObservationRequestLog, 'catalogue_meta': CatalogueMeta,
            'catalogue': Catalogue
        }
        ordered_tables = list(models.keys())

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
        if 'user_group' in data:
            for record in data['user_group']:
                # get id's from imported data
                old_user_id = record.get('user_id')
                old_group_id = record.get('group_id')
                
                # Find the user and group names from the imported data
                user_name = next((user['name'] for user in data['user'] if user['id'] == old_user_id), None)
                group_name = next((group['name'] for group in data['group'] if group['id'] == old_group_id), None)

                if user_name and group_name:
                    # Find the corresponding user and group in the current database
                    current_user = User.query.filter_by(name=user_name).first()
                    current_group = Group.query.filter_by(name=group_name).first()

                    if current_user and current_group:
                        # Check if the association already exists
                        stmt = select(user_group).where(and_(user_group.c.user_id == current_user.id, user_group.c.group_id == current_group.id))
                        exists = db.session.execute(stmt).first()
                        if not exists:
                            # Insert the new association
                            db.session.execute(user_group.insert().values(user_id=current_user.id, group_id=current_group.id))

        if 'role_group' in data:
            for record in data['role_group']:
                old_role_id = record.get('role_id')
                old_group_id = record.get('group_id')

                # Find the role and group names from the imported data
                role_name = next((role['name'] for role in data['role'] if role['id'] == old_role_id), None)
                group_name = next((group['name'] for group in data['group'] if group['id'] == old_group_id), None)

                if role_name and group_name:
                    # Find the corresponding role and group in the current database
                    current_role = Role.query.filter_by(name=role_name).first()
                    current_group = Group.query.filter_by(name=group_name).first()

                    if current_role and current_group:
                        # Check if the association already exists
                        stmt = select(role_group).where(and_(role_group.c.role_id == current_role.id, role_group.c.group_id == current_group.id))
                        exists = db.session.execute(stmt).first()
                        if not exists:
                            # Insert the new association
                            db.session.execute(role_group.insert().values(role_id=current_role.id, group_id=current_group.id))

        db.session.commit()
        flash('Data imported successfully. Existing records were ignored.')
    return redirect(url_for('admin.index'))

def record_to_dict(record):
    return {c.name: getattr(record, c.name) for c in record.__table__.columns}