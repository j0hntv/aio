FROM python:3.8

WORKDIR /opt/jaundice_rate

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./server.py" ]
