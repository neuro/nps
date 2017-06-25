FROM python:3.6-alpine

VOLUME /datasets
VOLUME /metadata_definitions
RUN pip install redis
ADD md_sync.py /
CMD ["python", "/md_sync.py"]