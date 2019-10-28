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

    import_sql = f'''

        SELECT * FROM {input_table}
        WHERE facdomain = 'Core Infrastructure and Transportation'
        OR (facdomain = 'Administration of Government'
        AND facsubgrp = 'Maintenance and Garages')
;

    '''
    # import data
    df = gpd.GeoDataFrame.from_postgis(import_sql, con=edm_engine, geom_col='geom')
    
    df.rename(columns = {'addressnum': 'geo_housenum', 'streetname': 'geo_streetname', 
                        'address': 'geo_address', 'boro': 'borough', 'bin': 'geo_bin',
                        'bbl': 'geo_bbl', 'commboard': 'geo_commboard', 'nta': 'geo_nta', 
                        'council': 'geo_council', 'schooldist': 'geo_schooldist', 
                        'policeprct': 'geo_policeprct', 'censtract': 'geo_censtract', 
                        'latitude': 'geo_latitude', 'longitude': 'geo_longitude', 
                        'xcoord': 'geo_xcoord', 'ycoord': 'geo_ycoord'}, inplace = True)
    
    df['geo_longitude'] = pd.to_numeric(df['geo_longitude'],errors='coerce')
    df['geo_latitude'] = pd.to_numeric(df['geo_latitude'],errors='coerce')
    df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.geo_longitude, df.geo_latitude))
    df['geom'] = df['geometry'].apply(lambda x: None if np.isnan(x.xy[0]) else str(x))

    os.system('echo "exporting table ..."')
    # export table to EDM_DATA
    exporter(df=df,
             output_table=output_table,
             DDL=DDL,
             sep='~',
             geo_column='geom')