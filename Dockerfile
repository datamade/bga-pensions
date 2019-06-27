FROM python:3.7-alpine
LABEL maintainer "DataMade <info@datamade.us>"
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
RUN mkdir /app
WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
