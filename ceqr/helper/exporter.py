from .engines import edm_engine
from sqlalchemy.types import TEXT

def exporter(df, output_table, DDL, con=edm_engine, sql='', chunksize=10000):
    # parse output table
    schema = output_table.split('.')[0]
    version = output_table.split('.')[1].replace('"', '')

    # check if schema exists
    con.connect().execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
    con.connect().execute(f'DROP TABLE IF EXISTS {output_table}')
    df[DDL.keys()].to_sql(version, con = con, schema=schema,
                            if_exists='replace', index=False, 
                            chunksize=chunksize)

    # additional queries or transformations:
    if sql != '':
        con.connect().execute(sql)
    else: pass

    # # Change to target DDL
    for key, value in DDL.items():
        con.connect().execute(f'ALTER TABLE {output_table} ALTER COLUMN {key} TYPE {value} USING ({key}::{value});')