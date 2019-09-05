FROM python:3.7-slim-buster

RUN adduser --system django
USER django

WORKDIR /home/django

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --user --no-warn-script-location
COPY . .
EXPOSE 8000

RUN [ "python", "./manage.py", "migrate" ]
RUN [ "python", "./manage.py", "loaddata", "sample_data" ]
ENTRYPOINT [ "python", "./manage.py", "runserver", "0.0.0.0:8000" ]

