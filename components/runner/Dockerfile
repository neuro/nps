FROM python:3.6-alpine

VOLUME /nps/datasets
ADD runner.py /runner.py
RUN pip install redis docker
CMD ["python3", "/runner.py"]