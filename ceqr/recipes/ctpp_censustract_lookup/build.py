from ceqr.helper.engines import recipe_engine, edm_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
from pathlib import Path
import geopandas as gpd
import pandas as pd
import time

geo_list = ['09001', '09005', '09009', '34003', '34013', '34017', 
    '34019', '34021', '34023', '34025', '34027', '34029', '34031', 
    '34035', '34037', '34039', '34041', '36005', '36027', '36047', 
    '36059', '36061', '36071', '36079', '36081', '36085', '36087', 
    '36103', '36105', '36111', '36119']

if __name__ == "__main__": 
    beg_ts = time.time()

    config = load_config(Path(__file__).parent/'config.json')
    
    input_table_ct = config['inputs'][0] 
    input_table_ny = config['inputs'][1] 
    input_table_nj = config['inputs'][2]

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

    # find out the unique census tracts between residential_geoid and work_geoid
    geoid_list = pd.concat([df.residential_geoid, df.work_geoid]).unique().astype('str')

    # turn the unique census tract list into a dataframe
    geoid_df = pd.DataFrame({'geoid':geoid_list})

    # merge the journey to work census tract list with shapefile
    df_geo = pd.merge(geoid_df, ct_shp[['geoid','centroid']], on = 'geoid')

    # df_geo['centroid'] = df_geo.centroid.astype('str')

    # exporter(df_geo, output_table, DDL,
    #         sql=f'UPDATE {output_table2} SET centroid=ST_SetSRID(centroid,4326)')
    exporter(df_geo, output_table, DDL)
