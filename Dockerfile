FROM python:3.12

RUN apt-get update && apt-get install -y libffi-dev libssl-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install -r requirements.txt

EXPOSE 9090

ENTRYPOINT python snap_reports_backend assets/config
