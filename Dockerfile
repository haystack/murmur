FROM python:2
ENV PYTHONUNBUFFERED 1
RUN apt-get update && apt-get install -y \
    telnet \
    default-mysql-client \
    cron && \
    rm -rf /var/lib/apt/lists/*
RUN mkdir -p /home/ubuntu/production/mailx
WORKDIR /home/ubuntu/production/mailx
COPY ./murmur-env/. /opt/murmur/
# COPY tasks-cron-docker /etc/cron.d/tasks-cron
# RUN crontab /etc/cron.d/tasks-cron
COPY requirements.txt /home/ubuntu/production/mailx/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir