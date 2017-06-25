FROM neurodebian:jessie
VOLUME /datasets
EXPOSE 1040
RUN apt-get update && apt-get install -y --no-install-recommends dcmtk python3-pip
RUN pip3 install pydicom redis
WORKDIR /home/dcmtk
ADD move.py move.py
RUN mkdir -p /tmp/datasets
CMD ["storescp", "--fork", "+xa", "-ac", "-aet", "NPS", "-dhl", "-od", "/tmp/datasets", "--exec-on-reception", "./move.py '#p/#f'", "+uf", "1040"]
