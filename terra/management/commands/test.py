from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import test

import os
import MySQLdb

class Command(test.Command):
    help = "Overrides built-in test command to set MySQL permissions on test database."

    def handle(self, *args, **options):
        # Django does not give the MySQL db user rights to create a test db.
        # Send appropriate database command to db server, but only in DEV.
        if os.getenv("DJANGO_RUN_ENV") == "dev":
            host = os.getenv("DJANGO_DB_HOST")
            passwd = os.getenv("MYSQL_ROOT_PASSWORD")
            prod_db = os.getenv("DJANGO_DB_NAME")
            test_db = os.getenv("DJANGO_TEST_DB_NAME")
            db_user = os.getenv("DJANGO_DB_USER")

            # Have to specify a db; prod exists, test doesn't
            con = MySQLdb.connect(host=host, user="root", passwd=passwd, db=prod_db)
            cur = con.cursor()
            sql = f"grant all privileges on {test_db}.* to '{db_user}'@'%';"
            cur.execute(sql)
            cur.close()
            con.close()

        super(Command, self).handle(*args, **options)
