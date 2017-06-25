FROM python:3.6-alpine

VOLUME /datasets
VOLUME /definitions
RUN pip install redis
ADD scan.py /
CMD ["python", "/scan.py"]