from .engines import edm_engine

def exporter(df, output_table, DDL, con=edm_engine, sql=''):
    # parse output table
    schema = output_table.split('.')[0]
    version = output_table.split('.')[1].repalce('"', '')

    # check if schema exists
    con.connect().execute(f'CREATE SCHEMA IF NOT EXISTS {schema}')
    df[DDL.keys()].to_sql(version, con = con, schema=schema, if_exists='replace', index=False)

    # additional queries or transformations:
    if sql != '':
        con.connect().execute(sql)
    else: pass

    # Change to target DDL
    for key, value in DDL.items():
        con.connect().execute(f"ALTER TABLE {schema}.{version} ALTER COLUMN {key} TYPE {value};")