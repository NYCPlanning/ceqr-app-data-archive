from ceqr.helper.engines import recipe_engine, edm_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
import pandas as pd
from pathlib import Path
import numpy as np
import geopandas as gpd
import os

def get_level(x):
    if x == 'PS': return 'ps'
    if x == 'MS': return 'is'

if __name__ == "__main__":
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    input_table_pct = config['inputs'][0]
    input_table_projections = config['inputs'][1]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']

    # import data
    pct = pd.read_sql(f'SELECT * FROM {input_table_pct}', con=recipe_engine)
    projections = pd.read_sql(f'SELECT * FROM {input_table_projections}', con=recipe_engine)

    # convert level value into lowercase
    # convert projections into a long list by level
    pct['level'] = pct['level'].apply(lambda x: get_level(x))
    pct.drop(columns=['ogc_fid'], inplace = True)
    projections = projections.drop(columns=['ogc_fid'])\
                             .melt(['district', 'school_year'], var_name='level', value_name='projections')

    # merge projections table with pct table
    # calculate projections by subdistrict
    df = pd.merge(projections, pct, how = 'inner', on = ['district', 'level'])
    df['projections'] = df['projections'].astype('int')
    df['multiplier'] = df['multiplier'].astype('float')
    df['projections'] = df['projections'] * df['multiplier']
    df['projections'] = df['projections'].astype('int')

    # pivot the df table by unstacking level
    df = df.reset_index().drop(columns=['index','multiplier'])
    df = df.set_index(['school_year', 'district','subdistrict', 'level'])\
           .projections.unstack()\
           .sort_values(by = ['district', 'subdistrict', 'school_year'])\
           .reset_index()
    # take the front year from the school_year
    df['school_year'] = df.school_year.apply(lambda x: x[:4]).astype('int')

    # export table to EDM_DATA
    exporter(df=df, 
             output_table=output_table,  
             DDL=DDL)