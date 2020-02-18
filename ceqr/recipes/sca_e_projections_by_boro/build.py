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
    input_table_projections = config['inputs'][0]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']

    # Import data
    projections = pd.read_sql(f'SELECT * FROM {input_table_projections}', con=recipe_engine)
    
    # Filter data to calculate projects at the high-school level
    hs_ = ['9','10','11','12']
    projections = projections[projections.projected.isin(hs_)].drop(columns=['ogc_fid'])

    # Change school_year field type to integer
    for school_year in projections.columns[3:]:
        projections[school_year] = projections[school_year].str.replace(",","").astype(int)

    # Reformat the table by melting and groupint by district
    df_hs = projections[projections.projected.isin(hs_)].drop(columns=['projected'])\
                                                        .groupby('district')\
                                                        .sum().reset_index()\
                                                        .melt('district', var_name='school_year', value_name='hs')

    # Create boro field
    b_to_d_dict = {'Manhattan':list(range(1,7)),
                    'Bronx':list(range(7,13)),
                    'Brooklyn':list(range(13,24)) + [32],
                    'Queens':list(range(24,31)),
                    'Staten Island':[31]}
    d_to_b_dict = dict((v1, k) for k, v in b_to_d_dict.items() for v1 in v)
    df_hs['borough'] = df_hs['district'].astype(int).map(d_to_b_dict)

    # Sum enrollment over boro
    df_boro = df_hs.groupby(['borough','school_year'], as_index=False).sum()
    df_boro['year'] = df_boro['school_year'].str[0:4]

    # Export table to EDM_DATA
    exporter(df=df_boro, 
             output_table=output_table,  
             DDL=DDL)