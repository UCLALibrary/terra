[![Build Status](https://travis-ci.com/UCLALibrary/terra.svg?branch=master)](https://travis-ci.com/UCLALibrary/terra) [![Coverage Status](https://coveralls.io/repos/github/UCLALibrary/terra/badge.svg?branch=master)](https://coveralls.io/github/UCLALibrary/terra?branch=master)

# TERRA
Travel & Entertainment Requests & Reports Application

## Developer Setup

### Local

1. Install Python 3.6
	- I recommend following this guide: https://docs.python-guide.org/
2. Open your terminal and open your projects directory

		$ cd /some/path/where/you/put/code

3. Pull this repo
	1. with SSH:

			$ git clone git@github.com:UCLALibrary/terra.git

	2. with HTTPS:

			$ git clone https://github.com/UCLALibrary/terra.git

4. Switch to the repo root

		$ cd terra

5. Create a Python virtual environment and activate it

		$ python3 -m venv ENV
		$ source ENV/bin/activate

6. Update pip and install the Python packages

		$ pip install --upgrade pip
		$ pip install -r requirements.txt

7. Install the pre-commit hook

		$ pre-commit install

8. Create the database tables

		$ python manage.py migrate

### Docker

1. Install docker and docker-compose.

2. Update local working copy as usual.

		$ git pull

3. Rebuild docker environment.

		$ docker-compose build

4. Start docker containers, running in the background.

		$ docker-compose up -d

***Note:*** Steps 3-4 can be combined, as

		$ docker-compose up --build -d

***Note:*** Starting the containers applies any pending migrations and loads the `sample_data` fixture.
It may take 15-20 seconds from the time the containers start until the application is available.

5. Create a django superuser if desired, or run any other manage.py command the same way.

		$ docker-compose exec django python manage.py createsuperuser

6. Connect to the application as usual, though if running docker in a VM you may need to forward ports to your host OS.

		http://127.0.0.1/dashboard or http://127.0.0.1/dashboard

7. Stop containers - shut down django and mysql

		$ docker-compose down

***Note:*** Database changes currently are not retained when the containers are stopped.

## Developer Tips

### Dealing with the database

#### Interaction

1. Create a superuser

		$ python manage.py createsuperuser

2. Work with the underlying database

		$ python manage.py dbshell

#### Migrations

When you change the Django models, you need to update the tables in the database by:

1. Creating a migration file

		$ python manage.py makemigrations

2. Running that migration

		$ python manage.py migrate

***Note:*** Always remember to check for new migrations when you pull down code from master.

### Testing Your Work

1. Use the Django REPL

		$ python manage.py shell

2. Run the development server (at http://localhost:8000)

		$ python manage.py runserver

3. Validate your code

		$ python manage.py check

4. Run the terra test suite

		$ python manage.py test terra

5. Use the sample data

		$ python manage.py loaddata sample_data

