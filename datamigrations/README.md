# Data Migrations vs Schema Migrations

The `flask db migrate` command only handles schema migrations. It is not
possible to migrate the actual data with `flask db migrate`. Instead the
scripts in this folder are used to perform certain data migration steps,
usually needed only once.

## Reservations

When upgrading to revision `Add observatory_reservation table` or higher
observatory_reservations need to be created with the following script:

```
python -m datamigrations add_observatory_reservations
```
