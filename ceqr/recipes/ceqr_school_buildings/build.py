from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
import pandas as pd
import geopandas as gpd
from pathlib import Path
import numpy as np
import os

def get_boro(d):

    BORO = {
        1: list(range(1,7)),
        2: list(range(7,13)),
        3: list(range(13,24))+[32],
        4: list(range(24,31)),
        5: [31]
    }
    for boro, district in BORO.items():
        if int(d) in district:
            return boro

if __name__ == "__main__":
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    input_table_lcgms = config['inputs'][0]
    input_table_bluebook = config['inputs'][1]
    input_table_subdistricts = config['inputs'][2]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']

    # import data
    bluebook = gpd.GeoDataFrame.from_postgis(f'''SELECT *, 'bluebook' AS source, \
                                                ST_TRANSFORM(ST_SetSRID(ST_MakePoint(x::NUMERIC, y::NUMERIC),2263),4326) AS geom \
                                                FROM {input_table_bluebook}''', con=recipe_engine, geom_col='geom')
    lcgms = gpd.GeoDataFrame.from_postgis(f'''SELECT *, 'lcgms' AS source FROM {input_table_lcgms}''',
                                                    con=recipe_engine, geom_col='geom')
    doe_school_subdistrict = gpd.GeoDataFrame.from_postgis(f'SELECT * FROM {input_table_subdistricts}', 
                                                    con=ceqr_engine, geom_col='geom')
    
    # perform column transformation for bluebook
    bluebook = bluebook[bluebook.org_level.isin(['PS','IS','HS','PSIS','ISHS'])]
    bluebook.rename(columns={'bldg_excl.': 'excluded', 'organization_name':'name'}, inplace = True)
    bluebook['borocode'] = bluebook.district.apply(lambda x: get_boro(x))
    bluebook['excluded'] = bluebook.excluded.apply(lambda x: True if x == 'Y' else False)
    bluebook['org_e'] = bluebook['org_e'].astype(float)
    bluebook['ps_%'] = bluebook['ps_%'].apply(lambda x: float(x[:-1])/100).astype(float)
    bluebook['ms_%'] = bluebook['ms_%'].apply(lambda x: float(x[:-1])/100).astype(float)
    bluebook['hs_%'] = bluebook['hs_%'].apply(lambda x: float(x[:-1])/100).astype(float)
    bluebook['pc'] = bluebook['pc'].fillna(0).astype(float).astype(int)
    bluebook['ic'] = bluebook['ic'].fillna(0).astype(float).astype(int)
    bluebook['hc'] = bluebook['hc'].fillna(0).astype(float).astype(int)
    bluebook['pe'] = bluebook.org_e * bluebook['ps_%']
    bluebook['pe'] = bluebook['pe'].fillna(0).astype(int)
    bluebook['ie'] = bluebook.org_e * bluebook['ms_%']
    bluebook['ie'] = bluebook['ie'].fillna(0).astype(int)
    bluebook['he'] = bluebook.org_e * bluebook['hs_%']
    bluebook['he'] = bluebook['he'].fillna(0).astype(int)

    # # only keep the records from lcgms not existing in bluebook
    # lcgms = lcgms[~(lcgms.org_id+lcgms.bldg_id).isin(bluebook.org_id+bluebook.bldg_id)]

    # # perform spatial join between lcgms and doe_school_subdistrict shapefile
    # lcgms = gpd.sjoin(lcgms, doe_school_subdistrict[['district','subdistrict', 'geom']], op='within')
    # lcgms = pd.DataFrame(lcgms)

    # # perform column transformation for lcgms
    # lcgms['borocode'] = lcgms.bbl.apply(lambda x: str(x)[0]).astype(int)
    # lcgms['bldg_name'] = lcgms.name
    # lcgms['excluded'] = False
    # lcgms['pc'] = 0
    # lcgms['ic'] = 0
    # lcgms['hc'] = 0

    # # merge lcgms and bluebook
    df = bluebook.iloc[:,:]
    
    os.system('echo "exporting table ..."')
    # export table to EDM_DATA
    exporter(df=df,
             output_table=output_table,  
             DDL=DDL,
             sep='~',
             geo_column='geom')