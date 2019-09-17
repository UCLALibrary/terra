#!/bin/bash

# Script to build and test the Django Terra app container

DOCKER_COMPOSE_TRAVIS="docker-compose -f .travis/docker-compose_travis_test.yml"

# Build the Django Terra App and Database images and start the containers
${DOCKER_COMPOSE_TRAVIS} up --build -d

# Install Converalls into the Django Terra container
${DOCKER_COMPOSE_TRAVIS} exec django pip install -q coveralls --user --no-warn-script-location

# Even though the build/up step above waits until the db is available, that's not always the case
# Keep trying to set db permissions for the django test user, so it can create a clean db for testing.
until ${DOCKER_COMPOSE_TRAVIS} exec db mysql -u root -pthis-is-a-fake-password -e "grant all privileges on test_terra.* to 'terrauser'@'%';"; do
  echo "Waiting for mysql to become available..."
  sleep 3
done

# For testing, to see what's running in the containers at this point
${DOCKER_COMPOSE_TRAVIS} top

# Another testing/debug command
${DOCKER_COMPOSE_TRAVIS} exec django ls -al

# Run the tests
${DOCKER_COMPOSE_TRAVIS} exec django /home/django/.local/bin/coverage run --source=terra manage.py test terra
