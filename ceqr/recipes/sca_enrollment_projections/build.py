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
    input_table_pct = config['inputs'][0]
    input_table_projections = config['inputs'][1]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']

    # import data
    sca_enrollment_pct_by_sd = pd.read_sql(f'SELECT * FROM {input_table_pct}', con=ceqr_engine)
    sca_enrollment_projections_by_sd = pd.read_sql(f'SELECT * FROM {input_table_projections}', con=ceqr_engine)

    # merge two tables and perform column transformation
    df = pd.merge(sca_enrollment_pct_by_sd, sca_enrollment_projections_by_sd, how='outer', on=['district'])
    df['school_year'] = df.school_year.apply(lambda x: x[:4])
    df['ps'] = df['ps'] * df.multiplier
    df['is'] = df['is'] * df.multiplier
    
    os.system('echo "exporting table ..."')
    # export table to EDM_DATA
    exporter(df=df, 
             output_table=output_table,  
             DDL=DDL)