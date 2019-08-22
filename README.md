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

***TODO***

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
