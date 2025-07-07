import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions, SetupOptions
import json
import logging

class PubsubmessageToJson(beam.DoFn):
    def process(self, element):
        try:
            message = json.loads(element.decode('utf-8'))

            # Handle single JSON object
            if isinstance(message, dict):
                yield self.format_record(message)

            # Handle list of JSON objects
            elif isinstance(message, list):
                for item in message:
                    if isinstance(item, dict):
                        yield self.format_record(item)
                    else:
                        logging.warning(f"Skipping non-dict item in list: {item}")
            else:
                logging.warning(f"Unexpected message type: {type(message)}")

        except Exception as e:
            logging.error(f"Failed to decode/process message: {element} → Error: {e}")

    def format_record(self, message):
        return {
            'count': int(message.get('count', 0)),
            'certificate_last_name': message.get('certificate_last_name'),
            'city': message.get('city'),
            'state': message.get('state'),
            'date_certified': message.get('date_certified'),
            'date_license_expiration': message.get('date_license_expiration'),
            'status': message.get('status'),
            'firms': message.get('firms'),
        }


def run():
    PROJECT_ID = 'newproject-464419'
    SUBSCRIPTION = 'projects/newproject-464419/subscriptions/tax-scraper-test-sub'
    STAGING_TABLE = 'newproject-464419.tax_data.tax_records_staging'
    BUCKET ='task-8-bucket'
    
    options = PipelineOptions(
        project=PROJECT_ID,
        runner='DataflowRunner',
        temp_location= f'gs://{BUCKET}/temp',
        streaming=True,
        region = 'asia-south1'
    )
    
    with beam.Pipeline(options=options) as p:
        (
            p
            | 'Read from Pub/Sub' >> beam.io.ReadFromPubSub(subscription=SUBSCRIPTION)
            | 'Convert to JSON' >> beam.ParDo(PubsubmessageToJson())
            | 'Write to BigQuery' >> beam.io.WriteToBigQuery(
                table=STAGING_TABLE,
                schema='count:INTEGER,certificate_last_name:STRING,city:STRING,state:STRING,date_certified:STRING,date_license_expiration:STRING,status:STRING,firms:STRING',
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED
            )
        )


if __name__ == '__main__':
    run()    
        

