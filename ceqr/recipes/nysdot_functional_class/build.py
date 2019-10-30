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
    input_boundary = config['inputs'][1]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']
    
    import_sql = f'''
            SELECT *, municipality_desc AS borough, wkb_geometry AS geom
            FROM {input_table} c
            WHERE wkb_geometry IS NOT NULL AND
            c.ogc_fid IN (
                SELECT a.ogc_fid FROM
                {input_table} a, (
                    SELECT ST_Union(wkb_geometry) As wkb_geometry
                    FROM {input_boundary}
                ) b
                WHERE ST_Contains(b.wkb_geometry, a.wkb_geometry)
                OR ST_Intersects(b.wkb_geometry, a.wkb_geometry)
            );
    '''
    # import data
    df = gpd.GeoDataFrame.from_postgis(import_sql, con=recipe_engine, geom_col='geom')
    
    os.system('echo "exporting table ..."')
    # export table to EDM_DATA
    
    exporter(df=df,
             output_table=output_table,
             DDL=DDL,
             sep='~',
             geo_column='geom')