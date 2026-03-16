import os

from google.cloud import bigquery

PROJECT_ID = os.environ["GCP_PROJECT_ID"]
DATASET = "manga_analytics"
TABLE = "manga_bronze"
RAW_FILE = "data/raw/manga.csv"


def load_client():
    return bigquery.Client(project=PROJECT_ID)


def build_job_config():
    return bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        allow_quoted_newlines=True,
        allow_jagged_rows=True,
    )


def load_bronze(client, job_config):
    table_ref = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    with open(RAW_FILE, "rb") as f:
        job = client.load_table_from_file(f, table_ref, job_config=job_config)
    job.result()
    return client.get_table(table_ref).num_rows


def main():
    client = load_client()
    job_config = build_job_config()
    row_count = load_bronze(client, job_config)
    print(f"Loaded {row_count} rows into {PROJECT_ID}.{DATASET}.{TABLE}")


if __name__ == "__main__":
    main()
