from airflow import models
from airflow.providers.google.cloud.transfers.bigquery_to_gcs import BigQueryToGCSOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
from google.cloud import secretmanager, storage
import pandas as pd
import sqlalchemy
import json
import tempfile

# CONFIG
PROJECT_ID = "newproject-464419"
BQ_DATASET = "ml_models"
BQ_TABLE = "auto-mpg-cleaned"
BUCKET_NAME = "auto-mpg-bucket"
GCS_OBJECT = "exports/auto_mpg.csv"
SECRET_NAME = "cloud-sql-credentials"
DB_TABLE_NAME = "auto_mpg_cleaned"

def get_db_engine():
    client = secretmanager.SecretManagerServiceClient()
    secret_path = f"projects/{PROJECT_ID}/secrets/{SECRET_NAME}/versions/latest"
    response = client.access_secret_version(request={"name": secret_path})
    secret = json.loads(response.payload.data.decode("UTF-8"))

    db_url = sqlalchemy.engine.URL.create(
        drivername="postgresql+psycopg2",  # Change to mysql+mysqldb if using MySQL
        username=secret["user"],
        password=secret["password"],
        host=secret["host"],
        database=secret["database"]
    )
    return sqlalchemy.create_engine(db_url)

def load_to_cloudsql(**kwargs):
    storage_client = storage.Client()
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(GCS_OBJECT)

    with tempfile.NamedTemporaryFile() as temp:
        blob.download_to_filename(temp.name)
        df = pd.read_csv(temp.name)
        engine = get_db_engine()
        df.to_sql(DB_TABLE_NAME, engine, if_exists='replace', index=False)

with models.DAG(
    dag_id="bq_to_gcs_and_sql_dag",
    schedule_interval=None,
    start_date=days_ago(1),
    catchup=False,
    tags=["bigquery", "cloudsql", "composer"],
) as dag:

    export_to_gcs = BigQueryToGCSOperator(
        task_id="export_bq_to_gcs",
        source_project_dataset_table=f"{PROJECT_ID}.{BQ_DATASET}.{BQ_TABLE}",
        destination_cloud_storage_uris=[f"gs://{BUCKET_NAME}/{GCS_OBJECT}"],
        export_format="CSV",
        field_delimiter=",",
        print_header=True,
    )

    gcs_to_cloudsql = PythonOperator(
        task_id="gcs_to_cloudsql",
        python_callable=load_to_cloudsql,
    )

    export_to_gcs >> gcs_to_cloudsql
