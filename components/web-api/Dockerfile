FROM python:3.6-alpine

RUN apk add --no-cache gcc linux-headers musl-dev
RUN pip install hug gunicorn gevent
WORKDIR /application
COPY nps_api.py /application/nps_api.py
CMD ["gunicorn", "-k", "gevent", "--worker-connections", "1000", "--bind", "0.0.0.0:80", "nps_api:__hug_wsgi__"]