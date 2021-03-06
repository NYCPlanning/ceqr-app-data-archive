from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
import pandas as pd
from pathlib import Path
import numpy as np
import geopandas as gpd
import os

def get_borocode(c):
    borocode = {
        "061": 1,
        "005": 2,
        "047": 3,
        "081": 4,
        "085": 5
    }
    return borocode.get(c, '')

if __name__ == "__main__":
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    input_table = config['inputs'][0]
    input_table_aadt = config['inputs'][1]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']

    # import data
    df = pd.read_sql(f'''SELECT * FROM {input_table} 
                        WHERE cou = '005' OR cou = '047' \
                        OR cou = '061' OR cou = '081' OR cou = '085';'''
                        , con=recipe_engine)
    aadt = pd.read_sql(f'SELECT rc_id AS rc_station, wkb_geometry AS geom \
                        FROM {input_table_aadt}', con = recipe_engine)

    df['borocode'] = df.cou.apply(lambda x: get_borocode(x))
    df['rc_station'] = df.rc_station.apply(lambda x: x.strip())
    df = pd.merge(df, aadt, how = 'left', on = 'rc_station')
    df['geom'] = df.geom.fillna('')

    os.system('echo "exporting table ..."')
    # export table to EDM_DATA
    exporter(df=df,
             output_table=output_table,
             DDL=DDL,
             geo_column = 'geom')