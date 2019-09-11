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

# For testing, to see what's running in the containers at this point
docker-compose top

# No longer necessary, since this succeeded in the loop above
#####docker-compose exec db mysql -u root -pthis-is-a-fake-password -e "grant all privileges on test_terra.* to 'terrauser'@'%';"


