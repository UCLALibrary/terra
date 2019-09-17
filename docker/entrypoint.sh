#!/bin/bash

# Check when database is ready for connections
until python -c 'import os ; import MySQLdb ; db=MySQLdb.connect(host=os.environ.get("DJANGO_DB_HOST"),user=os.environ.get("DJANGO_DB_USER"),passwd=os.environ.get("DJANGO_DB_PASSWD"),db=os.environ.get("DJANGO_DB_NAME"))' ; do
  echo "Database connection not ready - waiting"
  sleep 5
done

# Run database migrations
python ./manage.py migrate
python ./manage.py loaddata sample_data

# Build static files directory
python ./manage.py collectstatic

# Start the Gunicorn web server
gunicorn proj.wsgi:application
