FROM python:3.6-alpine

VOLUME /datasets
VOLUME /metadata_definitions
RUN pip install redis "elasticsearch>=2.0.0,<3.0.0"
ADD md_read.py /
ADD reindex.py /
CMD ["python", "/md_read.py"]