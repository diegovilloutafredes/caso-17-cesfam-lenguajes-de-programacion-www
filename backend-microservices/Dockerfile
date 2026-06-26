FROM python:3.12-slim

WORKDIR /app

# Dependencias compartidas entre todos los servicios
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código común y de los 6 servicios + gateway
# Para una imagen por servicio se separarían en Dockerfiles individuales;
# en sandbox compartimos imagen para simplicidad, cada container corre
# el `uvicorn ... .main:app` correspondiente vía `command` en docker-compose.
COPY shared/ ./shared/
COPY identity_service/ ./identity_service/
COPY patient_service/ ./patient_service/
COPY inventory_service/ ./inventory_service/
COPY prescription_service/ ./prescription_service/
COPY notification_service/ ./notification_service/
COPY report_service/ ./report_service/
COPY api_gateway/ ./api_gateway/

# Arranque para Railway (un servicio = los 7 procesos). En local no se usa:
# docker-compose levanta un contenedor por servicio con su propio `command`.
COPY railway-start.sh ./railway-start.sh
