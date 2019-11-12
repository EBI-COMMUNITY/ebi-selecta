FROM python:3-onbuild

LABEL Author="Blaise Alako" Email="blaise@ebi.ac.uk"

LABEL Description="SELECTA reporting  service" Vendor="EMBL-EBI" Version="1.0"

WORKDIR /usr/scr/app

COPY . .

CMD ["python3","scripts/selecta_processing_reports.py","-p","resources/properties.txt", "--db_live"]
