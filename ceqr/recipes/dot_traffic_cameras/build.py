from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
import pandas as pd
from pathlib import Path
import numpy as np
import geopandas as gpd
import os

if __name__ == "__main__":
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    input_table = config['inputs'][0]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']

    # import data
    df = gpd.GeoDataFrame.from_postgis(f'SELECT *, wkb_geometry AS geom FROM {input_table}', 
                                                    con=recipe_engine, geom_col='geom')

    os.system('echo "exporting table ..."')
    # export table to EDM_DATA
    exporter(df=df,
             output_table=output_table,
             DDL=DDL,
             sep='~',
             geo_column='geom')