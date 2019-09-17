#!/bin/bash

#
# Following a successful build of the Terra app image and tests of the app running in the container - this script will:
# 1. Tag the image
# 2. Push the image to the Docker Hub Registry
#
# These actions will only occur when changes are merged into the master branch
#

if [[ $TRAVIS_BRANCH == 'master' && $TRAVIS_PULL_REQUEST == 'false' ]]; then

  # Log-in to the Docker Registry
  echo ${DOCKER_PASSWORD} | docker login --username ${DOCKER_USERNAME} --password-stdin

  # Tag the terra image as 'latest'
  docker tag uclalibrary/terra:test uclalibrary/terra:latest

  # Push the terra image to the Docker Hub Registry
  docker push uclalibrary/terra:latest
fi
