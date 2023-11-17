#!/bin/bash

# Pick up any local changes to requirements.txt, which do *not* automatically get re-installed when starting the container.
# Do this only in dev environment!
if [ "$DJANGO_RUN_ENV" = "dev" ]; then
  pip install --no-cache-dir -r requirements.txt --user --no-warn-script-location
fi

# Check when database is ready for connections
until python -c 'import os ; import MySQLdb ; db=MySQLdb.connect(host=os.environ.get("DJANGO_DB_HOST"),user=os.environ.get("DJANGO_DB_USER"),passwd=os.environ.get("DJANGO_DB_PASSWD"),db=os.environ.get("DJANGO_DB_NAME"))' ; do
  echo "Database connection not ready - waiting"
  sleep 5
done

# Run database migrations
python ./manage.py migrate

# Load sample data when running in dev environment
if [ "$DJANGO_RUN_ENV" = "dev" ]; then
  echo "Loading sample data set..."
  python ./manage.py loaddata sample_data
fi

# Build static files directory, starting fresh each time
python ./manage.py collectstatic --no-input

if [ "$DJANGO_RUN_ENV" = "dev" ]; then
  python ./manage.py runserver 0.0.0.0:8000
else
  # Start the Gunicorn web server
  # Gunicorn cmd line flags:
  # -w number of gunicorn worker processes
  # -b IPADDR:PORT binding
  # --access-logfile where to send HTTP access logs (- is stdout)
  export GUNICORN_CMD_ARGS="-w 3 -b 0.0.0.0:8000 --access-logfile -"
  gunicorn proj.wsgi:application
fi
