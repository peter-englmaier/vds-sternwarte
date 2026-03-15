import sys
if len(sys.argv) != 2:
    print("""
        Usage:
            python -m datamigrations <migration>
        Example:
            python -m datamigrations add_observatory_reservations
        """)
    exit(1)