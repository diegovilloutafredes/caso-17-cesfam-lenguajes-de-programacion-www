-- Database per Service: una base PostgreSQL por servicio de dominio.
-- Se ejecuta una sola vez al inicializar el contenedor Postgres. La base 'cesfam'
-- (POSTGRES_DB) ya existe; aquí se crean las de cada servicio que persiste.
-- Report y el ApiGateway no persisten, por eso no tienen base.
CREATE DATABASE identity_db;
CREATE DATABASE patient_db;
CREATE DATABASE inventory_db;
CREATE DATABASE prescription_db;
CREATE DATABASE notification_db;
