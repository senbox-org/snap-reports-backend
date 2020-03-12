FROM python:3.7-alpine
RUN apk add --no-cache gfortran build-base libffi-dev libssl-dev 
COPY . .
RUN pip install -r requirements.txt
EXPOSE 9090
ENTRYPOINT python snap_reports_backend assets/config
