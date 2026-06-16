#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from tqdm import tqdm
from sqlalchemy import create_engine, text
import logging
import click

# set logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S', force=True
)
logger = logging.getLogger(__name__)

# set data config
dtype = {
    'VendorID': 'Int64',
    'passenger_count': 'Int64',
    'trip_distance': 'float',
    'RatecodeID': 'Int64',
    'store_and_fwd_flag': 'object',
    'PULocationID': 'Int64',
    'DOLocationID': 'Int64',
    'payment_type': 'Int64',
    'fare_amount': 'float',
    'extra': 'float',
    'mta_tax': 'float',
    'tip_amount': 'float',
    'tolls_amount': 'float',
    'improvement_surcharge': 'float',
    'total_amount': 'float',
    'congestion_surcharge': 'float',
}
yellow_dates = ['tpep_pickup_datetime', 'tpep_dropoff_datetime']
green_dates = ['lpep_pickup_datetime', 'lpep_dropoff_datetime']

def table_exists(table_name, engine):
    '''
    Check if a table exists in the database.
    '''
    with engine.connect() as conn:
        result = conn.execute(text(
            f"""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = '{table_name}'
            )
            """
        ))
        return result.scalar()

def csv_to_db(
        csv_url, db_name, engine, 
        dtype=dtype, parse_dates=None, 
        chunksize=100000, force_replace=False
    ):
    '''
    Reads a CSV file in chunks and inserts it into a PostgreSQL database table.
    '''
    # check if table exists, if yes, skip unless force flag is set
    if table_exists(db_name, engine):
        if not force_replace:
            logger.info(f'Table {db_name} already exists. Skipping.')
            return
        logger.info(f'Force replacing existing table {db_name}...')
    else:
        logger.info(f'Creating new table {db_name}...')
    
    # read csv data in chunks
    logger.info(f'Reading CSV file from {csv_url}...')
    df_iter = pd.read_csv(csv_url, dtype=dtype, parse_dates=parse_dates, iterator=True, chunksize=chunksize)

    # insert csv into db in chunks
    first = True
    for df_chunk in tqdm(df_iter, desc='Inserting data into the database'):
        if first: # create new table
            df_chunk.head(0).to_sql(name=db_name, con=engine, if_exists='replace')
            first = False
        df_chunk.to_sql(name=db_name, con=engine, if_exists='append')
    logger.info(f'Finished inserting data into {db_name} database table\n')

def validate_year_month(year, month):
    '''
    Validate year and month parameter to ensure validate date range for taxi data (2019-01 to 2021-07).
    '''
    if not (1 <= month <= 12):
        raise click.BadParameter(f'Month must be between 1 and 12, got {month}')
    if not (2019 <= year <= 2021):
        raise click.BadParameter(f'Year must be between 2019 and 2021, got {year}')
    if year == 2021 and month > 7:
        raise click.BadParameter('Latest data is 2021-07')

@click.command()
@click.option('--pg_user', envvar='PG_USER', default='root', help=f'PostgreSQL user (default=root)')
@click.option('--pg_pass', envvar='PG_PASS', default='root', help='PostgreSQL password (default=root)')
@click.option('--pg_host', envvar='PG_HOST', default='localhost', help='PostgreSQL host (default=localhost)')
@click.option('--pg_port', envvar='PG_PORT', default=5432, type=int, help='PostgreSQL port (default=5432)')
@click.option('--pg_db', envvar='PG_DB', default='ny_taxi', help='PostgreSQL database name (default=ny_taxi)')
@click.option('--year', envvar='YEAR', default=2020, type=int, help='Year of the taxi data to ingest (default=2020)')
@click.option('--month', envvar='MONTH', default=6, type=int, help='Month of the taxi data to ingest (default=6)')
@click.option('--chunksize', envvar='CHUNKSIZE', default=100000, type=int, help='Number of rows to read at a time when ingesting data (default=100000)')
@click.option('--force_replace', envvar='FORCE_REPLACE', default=False, type=bool, help='Force overwrite of existing table (default=False)')
def run(pg_user, pg_pass, pg_host, pg_port, pg_db, year, month, chunksize, force_replace):
    '''
    Main function to validate and ingest taxi data into PostgreSQL database.
    '''
    # validate year and month
    validate_year_month(year, month)

    # set csv url
    _base = 'https://github.com/DataTalksClub/nyc-tlc-data/releases/download'
    _yellow = '/yellow/yellow'
    _green = '/green/green'
    _file = f'_tripdata_{year}-{month:02d}.csv.gz'

    yellow_url = f'{_base}{_yellow}{_file}'
    green_url = f'{_base}{_green}{_file}'
    zones_url = f'{_base}/misc/taxi_zone_lookup.csv'

    # set db name
    yellow_db = f'yellow_taxi_data_{year}_{month:02d}'
    green_db = f'green_taxi_data_{year}_{month:02d}'
    zones_db = 'zones'

    # set sql url
    sql_url = f'postgresql+psycopg2://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}'

    # start sql engine
    engine = create_engine(sql_url)

    # ingest data into db
    csv_to_db(yellow_url, yellow_db, engine, parse_dates=yellow_dates, chunksize=chunksize, force_replace=force_replace)
    csv_to_db(green_url, green_db, engine, parse_dates=green_dates, chunksize=chunksize, force_replace=force_replace)
    csv_to_db(zones_url, zones_db, engine, chunksize=chunksize, force_replace=force_replace)

if __name__ == '__main__':
    run()