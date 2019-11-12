FROM python:3-onbuild

LABEL Author="Blaise Alako" Email="blaise@ebi.ac.uk"

LABEL Description="SELECTA Core executor service" Vendor="EMBL-EBI" Version="1.0"

WORKDIR /usr/scr/app

COPY . .

CMD ["python3","scripts/core_executor.py","-p","resources/properties.txt", "--db_live"]
