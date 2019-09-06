FROM python:3.7-slim-buster

RUN apt-get update -qq && apt-get install build-essential python3-dev default-libmysqlclient-dev -y -qq

RUN adduser --system django
USER django

WORKDIR /home/django

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --user --no-warn-script-location
COPY . .
EXPOSE 8000

CMD [ "sh", "docker/entrypoint.sh" ]
