from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
import pandas as pd
import geopandas as gpd
from pathlib import Path
import numpy as np
import os

if __name__ == "__main__":
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    input_table_bluebook = config['inputs'][0]
    input_table_lcgms = config['inputs'][1]
    input_table_subdistricts = config['inputs'][2]
    input_table_boro = config['inputs'][3]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']

    # import data
    bluebook = gpd.GeoDataFrame.from_postgis(f'''
                                                SELECT a.*, b.borocode, 'bluebook' AS source,\
                                                ST_TRANSFORM(ST_SetSRID(ST_MakePoint(a.x::NUMERIC, a.y::NUMERIC),2263),4326) AS geom\
                                                FROM {input_table_bluebook} a, {input_table_boro} b\
                                                WHERE ST_Within(ST_TRANSFORM(ST_SetSRID(ST_MakePoint(a.x::NUMERIC, a.y::NUMERIC),2263),4326),\
                                                    b.wkb_geometry)\
                                                AND a.org_id IS NOT NULL\
                                                ''', con=recipe_engine, geom_col='geom')

    #load lcgms records, excluding outsideNYC and ones existing in bluebook already
    lcgms = gpd.GeoDataFrame.from_postgis(f'''SELECT a.*, b.borocode, c.district, c.subdistrict, 'lcgms' AS source,\
                                                ST_SetSRID(ST_MakePoint(a.longitude::NUMERIC, a.latitude::NUMERIC),4326) AS geom\
                                                FROM {input_table_lcgms} a\
                                                LEFT JOIN {input_table_boro} b\
                                                ON ST_Within(ST_SetSRID(ST_MakePoint(a.longitude::NUMERIC, a.latitude::NUMERIC),4326),\
                                                    b.wkb_geometry)\
                                                LEFT JOIN {input_table_subdistricts} c\
                                                ON ST_Within(ST_SetSRID(ST_MakePoint(a.longitude::NUMERIC, a.latitude::NUMERIC),4326),\
                                                    c.wkb_geometry)\
                                                WHERE geographical_district_code !~* '00'\
                                                AND building_code||location_code NOT IN (\
                                                    SELECT DISTINCT bldg_id||org_id\
                                                    FROM sca_bluebook."2019"\
                                                    WHERE bldg_id||org_id IS NOT NULL)
                                                ''', con=recipe_engine, geom_col='geom')
    
    ## apply filter
    # bluebook = bluebook[bluebook.org_level.isin(['PS','IS','HS','PSIS','ISHS'])]

    # perform column transformation for bluebook
    bluebook.rename(columns={'bldg_excl.': 'excluded', 'organization_name':'name'}, inplace = True)
    bluebook['excluded'] = bluebook.excluded.apply(lambda x: True if x == 'Y' else False)
    bluebook['org_e'] = bluebook['org_e'].astype(float)
    bluebook['ps_%'] = bluebook['ps_%'].apply(lambda x: float(x[:-1])/100 if x != None else None).astype(float)
    bluebook['ms_%'] = bluebook['ms_%'].apply(lambda x: float(x[:-1])/100 if x != None else None).astype(float)
    bluebook['hs_%'] = bluebook['hs_%'].apply(lambda x: float(x[:-1])/100 if x != None else None).astype(float)
    bluebook['pc'] = bluebook['pc'].fillna(0).astype(float).astype(int)
    bluebook['ic'] = bluebook['ic'].fillna(0).astype(float).astype(int)
    bluebook['hc'] = bluebook['hc'].fillna(0).astype(float).astype(int)
    bluebook['pe'] = bluebook.org_e * bluebook['ps_%']
    bluebook['pe'] = bluebook['pe'].fillna(0).astype(int)
    bluebook['ie'] = bluebook.org_e * bluebook['ms_%']
    bluebook['ie'] = bluebook['ie'].fillna(0).astype(int)
    bluebook['he'] = bluebook.org_e * bluebook['hs_%']
    bluebook['he'] = bluebook['he'].fillna(0).astype(int)

    # rename the column names
    lcgms.rename(columns={'building_name':'bldg_name',
                          'building_id_number_(bin)':'bldg_id',
                          'location_code':'org_id',
                          'location_name':'name'}, inplace = True)

    # perform column transformation for lcgms
    lcgms['excluded'] = False
    lcgms['pc'] = 0
    lcgms['ic'] = 0
    lcgms['hc'] = 0
    lcgms['pe'] = 0
    lcgms['ie'] = 0
    lcgms['he'] = 0
    lcgms['org_level'] = None

    # merge lcgms and bluebook
    df = bluebook[DDL.keys()].append(lcgms[DDL.keys()])
    df['borocode'] = df['borocode'].fillna(0).astype('int')
    
    os.system('echo "exporting table ..."')
    # export table to EDM_DATA
    exporter(df=df,
             output_table=output_table,  
             DDL=DDL,
             sep='~',
             geo_column='geom')