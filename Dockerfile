FROM python:3.7-slim-buster

RUN apt-get update -qq && apt-get install build-essential python3-dev default-libmysqlclient-dev locales -y -qq
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && dpkg-reconfigure --frontend=noninteractive locales

RUN useradd -c "django app user" -d /home/django -s /bin/bash -m django
USER django

# Include python bin into django user's path
ENV PATH /home/django/.local/bin:${PATH}

# Gunicorn cmd line flags:
# -w number of gunicorn worker processes
# -b IPADDR:PORT binding
# --access-logfile where to send HTTP access logs (- is stdout)
ENV GUNICORN_CMD_ARGS -w 3 -b 0.0.0.0:8000 --access-logfile -

WORKDIR /home/django/terra

COPY --chown=django:django requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt --user --no-warn-script-location
COPY --chown=django:django . .

EXPOSE 8000

CMD [ "sh", "docker/entrypoint.sh" ]
