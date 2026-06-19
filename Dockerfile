# syntax=docker/dockerfile:1
# declare variables with default values
ARG CLEANBUILD=true
ARG GITCOMMIT=unknown
ARG GITCOMMITLONG=unknown
ARG APPVERSION=unknown

FROM python:3.14-alpine

# redeclare variables after from
ARG CLEANBUILD
ARG GITCOMMIT
ARG GITCOMMITLONG
ARG APPVERSION

RUN addgroup -S flask && adduser -S flask -G flask -h /vds

RUN apk update \
    && apk add build-base libpq libpq-dev

ENV FLASK_APP=app.py

WORKDIR /vds

COPY requirements-prod.txt ./requirements.txt
RUN pip3 install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY webapp webapp/
COPY migrations migrations/
COPY datamigrations datamigrations/
COPY prod.py app.py init-db.py docker-startup.sh make_celery.py ./

EXPOSE 5000/tcp
ENTRYPOINT [ "/bin/sh", "-c" ]
USER flask
CMD [ "./docker-startup.sh" ]
ENV CLEANBUILD=${CLEANBUILD} GITCOMMIT=${GITCOMMIT} GITCOMMITLONG=${GITCOMMITLONG} APPVERSION=${APPVERSION}
