FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# imagen única; cada servicio corre con su propio command en docker-compose
COPY shared/ ./shared/
COPY identity_service/ ./identity_service/
COPY patient_service/ ./patient_service/
COPY inventory_service/ ./inventory_service/
COPY prescription_service/ ./prescription_service/
COPY notification_service/ ./notification_service/
COPY report_service/ ./report_service/
COPY api_gateway/ ./api_gateway/

# arranque solo para Railway; en local compose define el command
COPY railway-start.sh ./railway-start.sh
