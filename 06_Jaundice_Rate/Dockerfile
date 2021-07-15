FROM python:3.8

COPY requirements.txt /opt/jaundice_rate/requirements.txt

RUN pip install --upgrade pip && pip install -r /opt/jaundice_rate/requirements.txt

COPY app/ /opt/jaundice_rate/app/

WORKDIR /opt/jaundice_rate/app/

CMD [ "python", "./server.py" ]
