FROM python:3.11-slim-bullseye

RUN apt-get update

# Set correct timezone
RUN ln -sf /usr/share/zoneinfo/America/Los_Angeles /etc/localtime

# Install dependencies needed to build psycopg2 python module and locales
RUN apt-get install -y gcc python3-dev libpq-dev pkg-config locales

# Set locale, originally required by mysqlclient and used in Django terra-specific code
RUN echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && dpkg-reconfigure --frontend=noninteractive locales

# Create django user and switch context to that user
RUN useradd -c "django app user" -d /home/django -s /bin/bash -m django
USER django

# Switch to application directory
WORKDIR /home/django/terra

# Copy application files to image, and ensure django user owns everything
COPY --chown=django:django . .

# Include local python bin into django user's path, mostly for pip
ENV PATH /home/django/.local/bin:${PATH}

# Make sure pip is up to date, and don't complain if it isn't yet
RUN pip install --upgrade pip --disable-pip-version-check

# Install requirements for this application
RUN pip install --no-cache-dir -r requirements.txt --user --no-warn-script-location

# Expose the typical Django port
EXPOSE 8000

CMD [ "sh", "docker_scripts/entrypoint.sh" ]
