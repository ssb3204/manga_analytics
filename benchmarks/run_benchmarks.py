import csv
import logging
import os
import subprocess
import time
from datetime import datetime, timezone

from google.cloud import bigquery

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

CONFIG = {
    "project_id": os.environ["GCP_PROJECT_ID"],
    "location": "US",
    "dataset": "manga_analytics",
    "benchmarks_dataset": "manga_analytics_benchmarks",
    "raw_file": "data/raw/manga.csv",
    "results_file": "dbt/seeds/benchmark_results.csv",
    "runs_per_variant": 3,
    "dbt_dir": "dbt",
}


def load_client(project_id: str) -> bigquery.Client:
    return bigquery.Client(project=project_id)


def detect_dbt_target() -> str:
    keyfile = "/secrets/gcp-key.json"
    if os.path.exists(keyfile):
        return "docker"
    return "dev"


def run_query_no_cache(
    client: bigquery.Client,
    query: str,
    test_name: str,
    variant: str,
) -> str:
    job_config = bigquery.QueryJobConfig(
        use_query_cache=False,
        labels={"benchmark": "true", "test_name": test_name, "variant": variant},
    )
    job = client.query(query, job_config=job_config)
    job.result()
    return job.job_id


def get_job_metrics(client: bigquery.Client, job_id: str) -> dict:
    time.sleep(5)
    query = f"""
    SELECT
        total_bytes_processed,
        total_slot_ms,
        TIMESTAMP_DIFF(end_time, start_time, SECOND) AS execution_time_s
    FROM `region-us`.INFORMATION_SCHEMA.JOBS
    WHERE job_id = '{job_id}'
    """
    rows = list(client.query(query).result())
    if not rows:
        logger.warning(f"job {job_id} not found in INFORMATION_SCHEMA.JOBS")
        return {
            "bytes_scanned": 0,
            "slot_time_ms": 0,
            "execution_time_s": 0,
        }
    row = rows[0]
    return {
        "bytes_scanned": row.total_bytes_processed or 0,
        "slot_time_ms": row.total_slot_ms or 0,
        "execution_time_s": row.execution_time_s or 0,
    }


def run_dbt_model(model_name: str) -> None:
    target = detect_dbt_target()
    cmd = [
        "dbt", "run",
        "--select", model_name,
        "--target", target,
        "--profiles-dir", ".",
    ]
    env = os.environ.copy()
    creds = env.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if creds and not os.path.isabs(creds):
        env["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(creds)
    logger.info(f"dbt run --select {model_name} --target {target}")
    result = subprocess.run(cmd, cwd=CONFIG["dbt_dir"], capture_output=True, text=True, env=env)
    if result.returncode != 0:
        logger.error(f"dbt run failed: {result.stdout}\n{result.stderr}")
        raise RuntimeError(f"dbt run failed for {model_name}")
    logger.info(f"dbt run {model_name} completed")


def get_latest_job_for_table(
    client: bigquery.Client,
    dataset: str,
    table_name: str,
) -> str:
    query = f"""
    SELECT job_id
    FROM `region-us`.INFORMATION_SCHEMA.JOBS
    WHERE job_type = 'QUERY'
        AND statement_type = 'CREATE_TABLE_AS_SELECT'
        AND destination_table.dataset_id = '{dataset}'
        AND destination_table.table_id LIKE '%{table_name}%'
    ORDER BY creation_time DESC
    LIMIT 1
    """
    rows = list(client.query(query).result())
    if not rows:
        return ""
    return rows[0].job_id


def build_benchmark_query(table_fqn: str) -> str:
    return f"""
    SELECT
        manga_type,
        COUNT(*) AS title_count,
        AVG(score) AS avg_score,
        SUM(members) AS total_members
    FROM `{table_fqn}`
    WHERE score IS NOT NULL
    GROUP BY manga_type
    ORDER BY title_count DESC
    """


def build_partition_query(table_fqn: str) -> str:
    return f"""
    SELECT
        manga_type,
        COUNT(*) AS title_count,
        AVG(score) AS avg_score
    FROM `{table_fqn}`
    WHERE start_date BETWEEN '2015-01-01' AND '2023-12-31'
        AND score IS NOT NULL
    GROUP BY manga_type
    ORDER BY avg_score DESC
    """


def count_rows_in_table(client: bigquery.Client, table_fqn: str) -> int:
    query = f"SELECT COUNT(*) AS cnt FROM `{table_fqn}`"
    rows = list(client.query(query).result())
    return rows[0].cnt


def run_test_materialization(client: bigquery.Client) -> list:
    project = CONFIG["project_id"]
    results = []

    view_fqn = f"{project}.manga_analytics_staging.stg_manga_clean"
    table_fqn = f"{project}.manga_analytics_benchmarks.stg_manga_clean_table"

    run_dbt_model("stg_manga_clean_table")
    build_job_id = get_latest_job_for_table(
        client, "manga_analytics_benchmarks", "stg_manga_clean_table"
    )
    if build_job_id:
        build_metrics = get_job_metrics(client, build_job_id)
        results.append({
            "test_name": "materialization_build",
            "variant": "table",
            "run_number": 1,
            **build_metrics,
            "row_count": count_rows_in_table(client, table_fqn),
            "measured_at": datetime.now(timezone.utc).isoformat(),
        })

    query_view = build_benchmark_query(view_fqn)
    query_table = build_benchmark_query(table_fqn)

    for run in range(1, CONFIG["runs_per_variant"] + 1):
        logger.info(f"materialization query — view run {run}")
        job_id = run_query_no_cache(client, query_view, "materialization_query", "view")
        metrics = get_job_metrics(client, job_id)
        results.append({
            "test_name": "materialization_query",
            "variant": "view",
            "run_number": run,
            **metrics,
            "row_count": count_rows_in_table(client, view_fqn),
            "measured_at": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(f"materialization query — table run {run}")
        job_id = run_query_no_cache(client, query_table, "materialization_query", "table")
        metrics = get_job_metrics(client, job_id)
        results.append({
            "test_name": "materialization_query",
            "variant": "table",
            "run_number": run,
            **metrics,
            "row_count": count_rows_in_table(client, table_fqn),
            "measured_at": datetime.now(timezone.utc).isoformat(),
        })

    return results


def run_test_partitioning(client: bigquery.Client) -> list:
    project = CONFIG["project_id"]
    results = []

    plain_fqn = f"{project}.manga_analytics_marts.fct_manga"
    part_fqn = f"{project}.manga_analytics_benchmarks.fct_manga_partitioned"

    run_dbt_model("fct_manga_partitioned")
    build_job_id = get_latest_job_for_table(
        client, "manga_analytics_benchmarks", "fct_manga_partitioned"
    )
    if build_job_id:
        build_metrics = get_job_metrics(client, build_job_id)
        results.append({
            "test_name": "partitioning_build",
            "variant": "partitioned",
            "run_number": 1,
            **build_metrics,
            "row_count": count_rows_in_table(client, part_fqn),
            "measured_at": datetime.now(timezone.utc).isoformat(),
        })

    query_plain = build_partition_query(plain_fqn)
    query_part = build_partition_query(part_fqn)

    for run in range(1, CONFIG["runs_per_variant"] + 1):
        logger.info(f"partitioning query — none run {run}")
        job_id = run_query_no_cache(client, query_plain, "partitioning_query", "none")
        metrics = get_job_metrics(client, job_id)
        results.append({
            "test_name": "partitioning_query",
            "variant": "none",
            "run_number": run,
            **metrics,
            "row_count": count_rows_in_table(client, plain_fqn),
            "measured_at": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(f"partitioning query — partitioned run {run}")
        job_id = run_query_no_cache(client, query_part, "partitioning_query", "partitioned")
        metrics = get_job_metrics(client, job_id)
        results.append({
            "test_name": "partitioning_query",
            "variant": "partitioned",
            "run_number": run,
            **metrics,
            "row_count": count_rows_in_table(client, part_fqn),
            "measured_at": datetime.now(timezone.utc).isoformat(),
        })

    return results


def split_csv(raw_path: str, output_path: str, n_rows: int) -> None:
    with open(raw_path, "r", encoding="utf-8") as src:
        reader = csv.reader(src)
        header = next(reader)
        rows = []
        for i, row in enumerate(reader):
            if i >= n_rows:
                break
            rows.append(row)

    with open(output_path, "w", encoding="utf-8", newline="") as dst:
        writer = csv.writer(dst)
        writer.writerow(header)
        writer.writerows(rows)

    logger.info(f"split CSV: {len(rows)} rows written to {output_path}")


def load_csv_to_table(
    client: bigquery.Client,
    csv_path: str,
    table_fqn: str,
    write_disposition: str,
) -> str:
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        autodetect=True,
        write_disposition=write_disposition,
        allow_quoted_newlines=True,
        allow_jagged_rows=True,
    )
    with open(csv_path, "rb") as f:
        job = client.load_table_from_file(f, table_fqn, job_config=job_config)
    job.result()
    return job.job_id


def run_merge_query(client: bigquery.Client, target_fqn: str, staging_fqn: str) -> str:
    merge_sql = f"""
    MERGE `{target_fqn}` AS target
    USING `{staging_fqn}` AS source
    ON target.manga_id = source.manga_id
    WHEN NOT MATCHED THEN
        INSERT ROW
    """
    job_config = bigquery.QueryJobConfig(
        use_query_cache=False,
        labels={"benchmark": "true", "test_name": "ingestion", "variant": "incremental"},
    )
    job = client.query(merge_sql, job_config=job_config)
    job.result()
    return job.job_id


def run_test_ingestion(client: bigquery.Client) -> list:
    project = CONFIG["project_id"]
    results = []

    bench_table = f"{project}.{CONFIG['benchmarks_dataset']}.manga_bronze_bench"
    staging_table = f"{project}.{CONFIG['benchmarks_dataset']}.manga_bronze_staging"
    partial_csv = "data/raw/manga_partial.csv"

    split_csv(CONFIG["raw_file"], partial_csv, 60000)

    for run in range(1, CONFIG["runs_per_variant"] + 1):
        logger.info(f"ingestion — full truncate run {run}")
        job_id = load_csv_to_table(
            client, CONFIG["raw_file"], bench_table, "WRITE_TRUNCATE"
        )
        metrics = get_job_metrics(client, job_id)
        results.append({
            "test_name": "ingestion",
            "variant": "full_truncate",
            "run_number": run,
            **metrics,
            "row_count": count_rows_in_table(client, bench_table),
            "measured_at": datetime.now(timezone.utc).isoformat(),
        })

        logger.info(f"ingestion — incremental merge run {run}")
        load_csv_to_table(client, partial_csv, bench_table, "WRITE_TRUNCATE")
        load_csv_to_table(client, CONFIG["raw_file"], staging_table, "WRITE_TRUNCATE")
        merge_job_id = run_merge_query(client, bench_table, staging_table)
        merge_metrics = get_job_metrics(client, merge_job_id)
        results.append({
            "test_name": "ingestion",
            "variant": "incremental_merge",
            "run_number": run,
            **merge_metrics,
            "row_count": count_rows_in_table(client, bench_table),
            "measured_at": datetime.now(timezone.utc).isoformat(),
        })

    try:
        os.remove(partial_csv)
        logger.info(f"cleaned up {partial_csv}")
    except OSError:
        pass

    return results


def write_results(all_results: list, output_path: str) -> None:
    fieldnames = [
        "test_name", "variant", "run_number",
        "bytes_scanned", "slot_time_ms", "execution_time_s",
        "row_count", "measured_at",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    logger.info(f"wrote {len(all_results)} results to {output_path}")


def print_summary(all_results: list) -> None:
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS SUMMARY")
    print("=" * 80)
    print(f"{'test_name':<25} {'variant':<18} {'run':<5} {'bytes':>12} {'slot_ms':>10} {'time_s':>8} {'rows':>8}")
    print("-" * 80)
    for r in all_results:
        print(
            f"{r['test_name']:<25} {r['variant']:<18} {r['run_number']:<5} "
            f"{r['bytes_scanned']:>12,} {r['slot_time_ms']:>10,} "
            f"{r['execution_time_s']:>8} {r['row_count']:>8,}"
        )
    print("=" * 80)


def main() -> None:
    client = load_client(CONFIG["project_id"])
    all_results = []

    logger.info("=== Test 1: Materialization (view vs table) ===")
    all_results.extend(run_test_materialization(client))

    logger.info("=== Test 2: Partitioning (none vs partitioned) ===")
    all_results.extend(run_test_partitioning(client))

    write_results(all_results, CONFIG["results_file"])
    print_summary(all_results)
    logger.info("all benchmarks complete")


if __name__ == "__main__":
    main()
