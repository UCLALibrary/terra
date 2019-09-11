#!/bin/sh

# Check when database is ready for connections
until python -c 'import MySQLdb ; db=MySQLdb.connect(host="db",user="terrauser",passwd="terra-fake-password",db="terra")' ; do
  echo "Database connection not ready - waiting"
  sleep 5
done

python ./manage.py migrate
python ./manage.py loaddata sample_data
python ./manage.py runserver 0.0.0.0:8000
