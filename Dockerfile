# syntax=docker/dockerfile:1

FROM python:3.12-alpine
ENV FLASK_APP=prod.py

WORKDIR /vds
COPY requirements.txt ./
RUN pip3 install --upgrade pip && pip install --no-cache-dir -r requirements.txt
EXPOSE 5000

COPY webapp webapp/
COPY migrations migrations/
COPY prod.py ./
COPY docker-startup.sh ./

CMD [ "./docker-startup.sh" ]
