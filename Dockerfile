FROM python:3.8
RUN apt-get update
RUN apt-get install -y libffi-dev libssl-dev 
COPY . .
RUN pip install -r requirements.txt
EXPOSE 9090
ENTRYPOINT python snap_reports_backend assets/config
