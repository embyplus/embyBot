FROM python:3.12-alpine
LABEL authors="TTLYTT0"

RUN apk add git build-base

COPY requirements.txt /opt
RUN pip install -r /opt/requirements.txt

RUN ln -sf /dev/stdout /opt/default.log

COPY ./bot /opt

WORKDIR /opt
ENTRYPOINT ["python", "app.py"]