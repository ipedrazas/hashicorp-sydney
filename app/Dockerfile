FROM python:2.7.11
MAINTAINER Ivan Pedrazas <ipedrazas@gmail.com>

RUN	pip install  \
    flask \
    flask-mysql \
    hvac


COPY . /app

CMD [ "python", "/app/meetup.py" ]