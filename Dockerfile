FROM python:3.7-slim-buster

RUN apt-get update -qq && apt-get install build-essential python3-dev default-libmysqlclient-dev -y -qq

RUN useradd -c "django app user" -d /home/django -s /bin/bash -m django
USER django

ENV PATH /home/django/.local/bin:${PATH}
ENV GUNICORN_CMD_ARGS -w 3 -b 0.0.0.0:8000

WORKDIR /home/django

COPY --chown=django:django . .

RUN pip install --no-cache-dir -r requirements.txt --user --no-warn-script-location

EXPOSE 8000

CMD [ "sh", "docker/entrypoint.sh" ]
