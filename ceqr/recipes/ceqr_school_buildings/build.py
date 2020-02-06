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
    input_table_bluebook = config['inputs'][0]
    input_table_lcgms = config['inputs'][1]
    input_table_subdistricts = config['inputs'][2]
    input_table_boro = config['inputs'][3]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']

    # import data
    # filter out Charter schools, Alternative high schools
    # Adult learning center and adult continuing education
    # Competitve highschools, City-wide G&T schools
    # and Pre-K centers
    bluebook = gpd.GeoDataFrame.from_postgis(f'''
                                                SELECT a.*, b.borocode, 'bluebook' AS source,\
                                                ST_TRANSFORM(ST_SetSRID(ST_MakePoint(a.x::NUMERIC, a.y::NUMERIC),2263),4326) AS geom\
                                                FROM {input_table_bluebook} a, {input_table_boro} b\
                                                WHERE ST_Within(ST_TRANSFORM(ST_SetSRID(ST_MakePoint(a.x::NUMERIC, a.y::NUMERIC),2263),4326),\
                                                    b.wkb_geometry)\
                                                AND a.org_id IS NOT NULL\
                                                AND(a.org_level IS NOT NULL\
                                                AND a.org_level != 'SPED'\
                                                AND a.org_level != 'OTHER')\
                                                AND a.charter IS NULL\
                                                AND a.organization_name !~* 'ALC'\
                                                AND a.organization_name !~* 'Alternative Learning'\
                                                AND a.org_id NOT IN ('Q950','M973')\
                                                AND a.organization_name !~* 'Adult'\
                                                AND a.org_id NOT IN ('X445','K449','K430','M692','X696','Q687','R605','M475')\
                                                AND a.org_id NOT IN ('M539', 'M334', 'K686', 'K682','Q300')\
                                                AND a.organization_name !~* 'pre-k'\
                                                ''', con=recipe_engine, geom_col='geom')

    # load lcgms records, excluding outsideNYC
    # apply filter
    lcgms = gpd.GeoDataFrame.from_postgis(f'''SELECT a.*, b.borocode, c.district, c.subdistrict, 'lcgms' AS source,\
                                            ST_SetSRID(ST_MakePoint(REPLACE(a.longitude,'NULL', '0')::NUMERIC,\
                                                REPLACE(a.latitude,'NULL', '0')::NUMERIC),4326) AS geom\
                                            FROM {input_table_lcgms} a\
                                            LEFT JOIN {input_table_boro} b\
                                            ON ST_Within(ST_SetSRID(ST_MakePoint(REPLACE(a.longitude,'NULL', '0')::NUMERIC,\
                                                REPLACE(a.latitude,'NULL', '0')::NUMERIC),4326), b.wkb_geometry)\
                                            LEFT JOIN {input_table_subdistricts} c\
                                            ON ST_Within(ST_SetSRID(ST_MakePoint(REPLACE(a.longitude,'NULL', '0')::NUMERIC,\
                                                REPLACE(a.latitude,'NULL', '0')::NUMERIC),4326), c.wkb_geometry)\
                                            WHERE system_code !~* '^75'
                                            AND system_code !~* '^84'
                                            AND building_code !~* ' AF '
                                            AND building_code !~* ' GYM '
                                                ''', con=recipe_engine, geom_col='geom')

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
                          'building_code':'bldg_id',
                          'location_code':'org_id',
                          'location_name':'name',
                          'address_line_1': 'address'}, inplace = True)
    # excluding sites in bluebook
    lcgms = lcgms[~(lcgms.org_id+lcgms.bldg_id).isin(bluebook.org_id+bluebook.bldg_id)]

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
