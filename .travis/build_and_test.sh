#!/bin/sh
# Try doing it all in one script since Travis is too non-deterministic.....

docker-compose up --build -d
docker-compose exec django pip install -q coveralls --user --no-warn-script-location
docker-compose top
docker-compose exec db mysql -u root -pthis-is-a-fake-password -e "grant all privileges on test_terra.* to 'terrauser'@'%';"

