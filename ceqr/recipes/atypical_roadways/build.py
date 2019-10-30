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

        SELECT street AS streetname, segmentid, streetwidth_min,streetwidth_max, 
            lzip AS left_zipcode, rzip AS right_zipcode,
            LEFT(StreetCode, 1) AS borocode, nodelevelf, nodelevelt,
            featuretyp, trafdir, nullif(number_total_lanes, '  ')::NUMERIC AS number_total_lanes, 
            trim(bikelane) AS bikelane, wkb_geometry AS geom
        FROM {input_table}
        WHERE ((nodelevelf!= 'M' AND nodelevelf!= '*' AND nodelevelf!= '$')
        OR (nodelevelt!= 'M' AND nodelevelt!= '*' AND nodelevelt!= '$'))
        AND trafdir != 'P'
        AND featuretyp != '1'
        AND (nullif(number_total_lanes, '  ')::NUMERIC != 1
        OR nullif(number_total_lanes, '  ')::NUMERIC IS NULL)
        AND trim(bikelane) != '1'
        AND trim(bikelane) != '2'
        AND trim(bikelane) != '4'
        AND trim(bikelane) != '9';

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