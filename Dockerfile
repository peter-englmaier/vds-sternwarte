# syntax=docker/dockerfile:1

FROM python:3.12

WORKDIR /vds

COPY requirements.txt ./
RUN pip3 install --upgrade pip && pip install --no-cache-dir -r requirements.txt
EXPOSE 5000

COPY webapp webapp/
COPY prod.py ./

CMD ["gunicorn", "prod:app", "-b", "0.0.0.0:5000", "-w", "4"]
