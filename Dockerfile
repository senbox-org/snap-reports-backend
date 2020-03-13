FROM python:3.8
RUN apt install build-base libffi-dev libssl-dev -y
COPY . .
RUN pip install -r requirements.txt
EXPOSE 9090
ENTRYPOINT python snap_reports_backend assets/config
