from ceqr.helper.engines import recipe_engine, edm_engine
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
    pct = pd.read_sql(f'SELECT district, subdistrict, level, multiplier FROM {input_table_pct}', con=recipe_engine)
    projections = pd.read_sql(f'SELECT * FROM {input_table_projections}', con=recipe_engine)
    
    # filter data to calculate projects by school level
    target = ['PK','K','1','2','3','4','5','6','7','8']
    ps_ = target[:7]
    is_ = target[7:]
    projections = projections[projections.projected.isin(target)].drop(columns=['ogc_fid'])

    # change school_year field type to integer
    for school_year in projections.columns[2:]:
        projections[school_year] = projections[school_year].astype(int)

    # reformat the projections table
    df_ps = projections[projections.projected.isin(ps_)].drop(columns=['projected'])\
                                                        .groupby('district')\
                                                        .sum().reset_index()\
                                                        .melt('district', var_name='school_year', value_name='ps')
    df_is = projections[projections.projected.isin(is_)].drop(columns=['projected'])\
                                                        .groupby('district')\
                                                        .sum().reset_index()\
                                                        .melt('district', var_name='school_year', value_name='is')

    projections = pd.merge(df_ps, df_is, on =['district','school_year'])

    # reformat the subdistrict percentage table
    pct['multiplier'] = pct.multiplier.apply(lambda x: float(x[:-1])/100).astype(float)
    pct = pct.groupby(['district', 'subdistrict', 'level'])\
             .multiplier.sum().unstack(fill_value=0).reset_index()\
             .rename(columns={'MS':'is_multiplier', 'PS':'ps_multiplier'})

    # merge two tables and perform column transformation
    df = pd.merge(pct, projections, how='outer', on=['district'])\
           .sort_values(by=['district','subdistrict'])
    df['school_year'] = df.school_year.apply(lambda x: x[:4])
    df['ps'] = df['ps'] * df.ps_multiplier
    df['is'] = df['is'] * df.is_multiplier
    df['ps'] = round(df['ps'], 0).astype(int)
    df['is'] = round(df['is'], 0).astype(int)

    # export table to EDM_DATA
    exporter(df=df, 
             output_table=output_table,  
             DDL=DDL)