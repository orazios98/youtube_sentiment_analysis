FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY bin/* ./
COPY python-manager.sh .
ENTRYPOINT [ "./python-manager.sh" ]

