FROM python:3.6-alpine
RUN pip install pydicom python-dateutil
COPY read_dicom.py /root/read_dicom.py
WORKDIR /root
CMD ["python", "read_dicom.py"]