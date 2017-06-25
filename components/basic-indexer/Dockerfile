FROM python:3.6-alpine
RUN pip install python-dateutil
COPY stats.py /root/stats.py
WORKDIR /root
CMD ["python", "stats.py"]