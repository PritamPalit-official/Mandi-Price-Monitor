"""One small layer so the same code runs on local DuckDB (default) or BigQuery."""
import os

import pandas as pd

from mandi import config


def _dates_as_date(df):
    df = df.copy()
    for col in df.columns:
        if str(df[col].dtype).startswith("datetime64"):
            df[col] = df[col].dt.date
    return df


def _duck():
    import duckdb
    os.makedirs(os.path.dirname(config.DUCKDB_PATH) or ".", exist_ok=True)
    con = duckdb.connect(config.DUCKDB_PATH)
    con.execute("CREATE SCHEMA IF NOT EXISTS mandi")
    return con


def _bq():
    from google.cloud import bigquery
    return bigquery.Client(project=config.GCP_PROJECT)


def _sql_for_engine(text):
    return text.replace("mandi.", f"{config.BQ_DATASET}.") if config.ENGINE == "bigquery" else text


def load(df, name):
    df = _dates_as_date(df)
    if config.ENGINE == "duckdb":
        con = _duck()
        con.register("df_tmp", df)
        con.execute(f"CREATE OR REPLACE TABLE mandi.{name} AS SELECT * FROM df_tmp")
        con.close()
    else:
        from google.cloud import bigquery
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
        _bq().load_table_from_dataframe(
            df, f"{config.GCP_PROJECT}.{config.BQ_DATASET}.{name}", job_config=job_config).result()


def run_sql_file(path):
    with open(path, encoding="utf-8") as f:
        text = _sql_for_engine(f.read())
    statements = [s.strip() for s in text.split(";") if s.strip()]
    if config.ENGINE == "duckdb":
        con = _duck()
        for statement in statements:
            con.execute(statement)
        con.close()
    else:
        for statement in statements:
            _bq().query(statement).result()


def query(sql):
    sql = _sql_for_engine(sql)
    if config.ENGINE == "duckdb":
        con = _duck()
        out = con.execute(sql).df()
        con.close()
        return out
    return _bq().query(sql).to_dataframe()
