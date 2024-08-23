[![Build Status](https://img.shields.io/github/actions/workflow/status/UCLALibrary/terra/run_tests.yml)] [![Coverage Status](https://img.shields.io/coverallsCoverage/github/UCLALibrary/terra)]

# TERRA
Travel & Entertainment Requests & Reports Application

## Developer Setup

### Local

1. Install Python 3.7
	- I recommend following this guide: https://docs.python-guide.org/
2. Open your terminal and open your projects directory

		$ cd /some/path/where/you/put/code

3. Clone this repo
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

2. Clone the repo.

	1. with SSH:

			$ git clone git@github.com:UCLALibrary/terra.git

	2. with HTTPS:

			$ git clone https://github.com/UCLALibrary/terra.git

3. Rebuild docker environment.  This will pull images from Docker Hub.

		$ docker compose build

4. Start docker containers, running in the background.

		$ docker compose up -d

***Note:*** Steps 3-4 can be combined, as

		$ docker compose up --build -d

***Note:*** Starting the containers applies any pending migrations and loads the `sample_data` fixture.
It may take 15-20 seconds from the time the containers start until the application is available.

5. Create a django superuser if desired, or run any other manage.py command the same way.

		$ docker compose exec django python manage.py createsuperuser

6. Connect to the application as usual, though if running docker in a VM you may need to forward ports to your host OS.

		http://127.0.0.1/ or http://127.0.0.1:8000/ (as a regular user)
		http://127.0.0.1/admin/ or http://127.0.0.1:8000/admin/ (as a super/admin user)

7. Stop containers - shut down django and mysql

		$ docker compose down

***Note:*** Database changes are not retained when the containers are stopped.

## Developer Tips

### Dealing with the database

#### Interaction

1. Create a superuser

		$ docker compose exec django python manage.py createsuperuser

2. Work with the underlying database (does not currently work in Docker environment)

		$ docker compose exec django python manage.py dbshell

#### Migrations

When you change the Django models, you need to update the tables in the database by:

1. Creating a migration file

		$ docker compose exec django python manage.py makemigrations

2. Running that migration

		$ docker compose exec django python manage.py migrate

***Note:*** Always remember to check for new migrations when you pull down code from master.  Or restart the Docker containers to apply all migrations.

### Testing Your Work

1. Use the Django REPL

		$ docker compose exec django python manage.py shell

2. Validate your code

		$ docker compose exec django python manage.py check

3. Functional tests: Run the terra test suite

		$ docker compose exec django python manage.py test terra

4. Static code analysis: Run pyflakes

		$ docker compose exec django pyflakes terra

5. Load different data (sample data is loaded automatically if working in Docker environment)

		$ docker compose exec django python manage.py flush
		$ docker compose exec django python manage.py loaddata data_file (must be in terra/fixtures directory)

6. View the logs

		$ docker compose logs django (or docker compose logs db)
		$ docker compose logs -f django (to tail the logs continuously; press CTRL-C to exit)
