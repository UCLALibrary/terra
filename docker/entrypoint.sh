#!/bin/bash

# Check when database is ready for connections
until python -c 'import os ; import MySQLdb ; db=MySQLdb.connect(host=os.environ.get("DJANGO_DB_HOST"),user=os.environ.get("DJANGO_DB_USER"),passwd=os.environ.get("DJANGO_DB_PASSWD"),db=os.environ.get("DJANGO_DB_NAME"))' ; do
  echo "Database connection not ready - waiting"
  sleep 5
done

# Run database migrations
python ./manage.py migrate

# Load sample data when running in dev environment
if [ "$DJANGO_RUN_ENV" == "dev" ]; then
  echo "Loading sample data set..."
  python ./manage.py loaddata sample_data
fi

# Build static files directory, starting fresh each time
python ./manage.py collectstatic --clear --no-input

# Start the Gunicorn web server
gunicorn proj.wsgi:application
