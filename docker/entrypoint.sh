#!/bin/sh

# Check when database is ready for connections
until python -c 'import MySQLdb ; db=MySQLdb.connect(host="db",user="terrauser",passwd="terra-fake-password",db="terra")' ; do
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
