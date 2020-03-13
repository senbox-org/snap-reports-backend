FROM python:3.6-alpine
RUN apk add --no-cache gfortran build-base libffi-dev openssl-dev 
COPY . .
RUN pip install -r requirements.txt
EXPOSE 9090
ENTRYPOINT python snap_reports_backend assets/config
