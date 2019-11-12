FROM python:3-onbuild

LABEL Author="Blaise Alako" Email="blaise@ebi.ac.uk"

LABEL Description="SELECTA selection to attribure service" Vendor="EMBL-EBI" Version="1.0"

WORKDIR /usr/scr/app

COPY . .

CMD ["python3","scripts/selection_to_attribute.py","-p","resources/properties.txt", "--db_live"]
