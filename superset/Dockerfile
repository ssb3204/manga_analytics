FROM apache/superset:4.1.1
USER root
RUN pip install sqlalchemy-bigquery
USER superset
COPY superset_config.py /app/pythonpath/superset_config.py
