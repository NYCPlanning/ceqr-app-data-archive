from ceqr.helper.engines import recipe_engine, edm_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
from shapely.wkt import loads, dumps
from pathlib import Path
import geopandas as gpd
import pandas as pd
import time

if __name__ == "__main__": 
    beg_ts = time.time()

    config = load_config(Path(__file__).parent/'config.json')
    
    input_table_ct = config['inputs'][0] 
    input_table_ny = config['inputs'][1] 
    input_table_nj = config['inputs'][2]
    ctpp_journey_to_work = config['inputs'][3]

    output_table = config['outputs'][0]['output_table'] #ctpp_censustract_lookup
    DDL = config['outputs'][0]['DDL']

    ct = gpd.GeoDataFrame.from_postgis(f'SELECT * FROM {input_table_ct}', con=recipe_engine, geom_col='wkb_geometry' )
    ny = gpd.GeoDataFrame.from_postgis(f'SELECT * FROM {input_table_ny}', con=recipe_engine, geom_col='wkb_geometry' )
    nj = gpd.GeoDataFrame.from_postgis(f'SELECT * FROM {input_table_nj}', con=recipe_engine, geom_col='wkb_geometry' )

    # merge the 3 states shapefile together
    ct_shp = ct.append(ny).append(nj)

    # calculate the centroid for each census tract
    ct_shp['centroid'] = ct_shp['wkb_geometry'].centroid

    # rename the geoid column
    ct_shp.rename(columns={'GEOID':'geoid'}, inplace=True)

    df = pd.read_sql(f'''
                    SELECT residential_geoid, work_geoid
                    FROM {ctpp_journey_to_work}
                    ''', con=edm_engine)

    # find out the unique census tracts between residential_geoid and work_geoid
    geoid_list = pd.concat([df.residential_geoid, df.work_geoid]).unique().astype('str')

    # turn the unique census tract list into a dataframe
    geoid_df = pd.DataFrame({'geoid':geoid_list})

    # merge the journey to work census tract list with shapefile
    df_geo = pd.merge(geoid_df, ct_shp[['geoid','centroid']], on = 'geoid')
    df_geo['centroid'] = df_geo['centroid'].apply(lambda x: loads(dumps(x)).wkt)

    exporter(df_geo, output_table, DDL,
            sql=f'UPDATE {output_table} SET centroid=ST_SetSRID(centroid,4326)')