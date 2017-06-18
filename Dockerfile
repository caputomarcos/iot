FROM python:2.7

MAINTAINER Marcos Caputo "caputo.marcos@gmail.com"

RUN mkdir -p /src/iot

COPY ./iot /src/iot
COPY requirements.txt /src/iot

WORKDIR /src/iot

RUN pip install -r requirements.txt

ENTRYPOINT ["python"]

CMD ["app.py"]
