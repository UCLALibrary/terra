#!/bin/sh
# Try doing it all in one script since Travis is too non-deterministic.....

docker-compose up --build -d
docker-compose exec django pip install -q coveralls --user --no-warn-script-location

# Even though the build/up step above waits until the db is available, that's not always the case
# Keep trying to set db permissions for the django test user, so it can create a clean db for testing.
until docker-compose exec db mysql -u root -pthis-is-a-fake-password -e "grant all privileges on test_terra.* to 'terrauser'@'%';"; do
  echo "Waiting for mysql to become available..."
  sleep 3 
done

# When building in Travis, the host directory is owned by Travis.  The volume mount in the django Docker
# container apparently reflects that, leading to permissions problems inside the container when running tests.
# Reset permissions in the container before running tests.
# django user doesn't have rights to change these permissions in the container (and sudo currently not installed in container).
#docker-compose exec django chown -R django:django /home/django

# Change permissions in host: keep travis ownership but relax permissions.
# Do this only if running in Travis, to avoid problems locally.
if [ "$TRAVIS" = "true" ]; then
  chmod -R 777 .
fi

# Run the tests
docker-compose exec django /home/django/.local/bin/coverage run --source=terra manage.py test terra

