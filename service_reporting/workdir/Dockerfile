FROM python:3-onbuild

WORKDIR /usr/scr/app
#COPY ./requirements.txt .
COPY . .

#COPY . .
#ENTRYPOINT ["python","selection_to_attribute.py","-p","properties.txt"]
CMD ["python3","scripts/selection_to_attribute.py","-p","resources/properties.txt"]
