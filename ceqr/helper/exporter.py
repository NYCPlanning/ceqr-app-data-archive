from .engines import edm_engine, psycopg2_connect
from sqlalchemy.types import TEXT
import io
import psycopg2
import logging
import os

def exporter(df, output_table, DDL, 
            con=edm_engine, sql='', sep=',', 
            geo_column='', SRID=4326):
    # parse output table
    schema = output_table.split('.')[0]
    version = output_table.split('.')[1].replace('"', '')
    
    # psycopg2 connections
    db_connection = psycopg2_connect(con.url)
    db_cursor = db_connection.cursor()
    str_buffer = io.StringIO() 

    columns = [i.strip('"') for i in DDL.keys()]
    column_definitions = ','.join([f'"{key}" {value}' for key,value in DDL.items()])

    # Create table
    create = f'''
    CREATE SCHEMA IF NOT EXISTS {schema};
    DROP TABLE IF EXISTS {output_table};
    CREATE TABLE {output_table} (
        {column_definitions}
    );
    '''

    con.connect().execute(create)
    con.dispose()

    os.system(f'\necho "exporting table {output_table} ..."')

    # add SRID to spatial columns
    df = df[columns]

    if geo_column != '':
        df.loc[:, geo_column] = df.loc[:, geo_column].apply(lambda x: f'SRID={SRID};{x}' if x else '')
    else: 
        pass
    # export
    df.to_csv(str_buffer, sep=sep, header=False, index=False)
    str_buffer.seek(0)
    db_cursor.copy_from(str_buffer, output_table, sep=sep, null='')
    db_cursor.connection.commit()

    # additional queries or transformations:
    if sql != '':
        con.connect().execute(sql)
        con.dispose()
    else: pass

    str_buffer.close()
    db_cursor.close()
    db_connection.close()

def exporter_classic(df, output_table, DDL, con=edm_engine, sql='', chunksize=10000):
    # parse output table
    schema = output_table.split('.')[0]
    version = output_table.split('.')[1].replace('"', '')

    # check if schema exists
    con.connect().execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
    con.connect().execute(f'DROP TABLE IF EXISTS {output_table}')

    columns = [i.strip('"') for i in DDL.keys()]

    os.system(f'\necho "exporting table {output_table} ..."')

    df[columns].to_sql(version, con = con, schema=schema,
                            if_exists='replace', index=False, 
                            chunksize=chunksize)

    # additional queries or transformations:
    if sql != '':
        con.connect().execute(sql)
    else: pass

    # # Change to target DDL
    for key, value in DDL.items():
        con.connect().execute(f'ALTER TABLE {output_table} ALTER COLUMN "{key}" TYPE {value} USING ("{key}"::{value});')