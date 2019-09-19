from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
import pandas as pd
from pathlib import Path
import numpy as np
import geopandas as gpd

if __name__ == "__main__":
    # Load configuration (note: please use relative paths)
    config = load_config(Path(__file__).parent/'config.json')
    input_table_lcgms = config['inputs'][0]
    input_table_bluebook = config['inputs'][1]
    input_table_subdistricts = config['inputs'][2]
    output_table = config['outputs'][0]['output_table']
    output_table_version = config['outputs'][0]['output_table'].split('.')[1].strip('\"')
    DDL = config['outputs'][0]['DDL']

    # import data
    sca_bluebook = pd.read_sql(f'select * from {input_table_bluebook}', con=ceqr_engine)
    doe_lcgms = gpd.GeoDataFrame.from_postgis(f'SELECT * FROM {input_table_lcgms}', con=ceqr_engine, geom_col='geom' )
    doe_school_subdistrict = gpd.GeoDataFrame.from_postgis(f'SELECT * FROM {input_table_subdistricts}', con=ceqr_engine, geom_col='geom' )
    
    # rename column names
    if output_table_version == '2017': 
        sca_bluebook.columns = ['ogc_fid', 'cartodb_id', 'district', 'subdistrict', 'borocode',
                                'bldg_name', 'excluded', 'bldg_id', 'org_id', 'org_level', 'name',
                                'address', 'pc', 'pe', 'ic', 'ie',
                                'hc', 'he', 'geom']
        doe_lcgms.columns = ['ogc_fid', 'cartodb_id', 'org_id', 'bldg_id', 'org_level', 'grades',
                                'pe', 'ie', 'he', 'name', 'address', 'bbl', 'lat',
                                'lng', 'geom']
    else: # output table version is later than 2017
        sca_bluebook.columns = ['ogc_fid', 'cartodb_id', 'district', 'subdistrict', 'borocode',
                                'bldg_name', 'excluded', 'bldg_id', 'org_id', 'org_level', 'name',
                                'address', 'pc', 'pe', 'ic', 'ie', 'hc', 'he', 'x', 'y', 'geom']
        doe_lcgms.columns = ['ogc_fid', 'cartodb_id', 'org_id', 'bldg_id', 'org_level', 'name',
                            'address', 'bbl', 'lat', 'lng', 'pe', 'ie', 'he','grades', 'geom']
    
    # add source column
    doe_lcgms['source'] = 'lcgms'
    sca_bluebook['source'] = 'bluebook'

    # only keep the records from doe_lcgms not existing in sca_bluebook
    doe_lcgms = doe_lcgms[~(doe_lcgms.org_id+doe_lcgms.bldg_id).isin(sca_bluebook.org_id+sca_bluebook.bldg_id)]

    # perform spatial join between lcgms and doe_school_subdistrict shapefile
    lcgms_district_lookup = gpd.sjoin(doe_lcgms[['org_id','bldg_id','geom']], doe_school_subdistrict[['district','subdistrict', 'geom']], op='within')
    doe_lcgms = pd.DataFrame(doe_lcgms)
    lcgms_district_lookup = pd.DataFrame(lcgms_district_lookup)
    doe_lcgms = pd.merge(doe_lcgms, lcgms_district_lookup[['org_id','bldg_id','district','subdistrict']], on=['org_id','bldg_id'])
     

    # perform column transformation for doe_lcgms 
    doe_lcgms['borocode'] = doe_lcgms.bbl.apply(lambda x: str(x)[0]).astype(int)
    doe_lcgms['bldg_name'] = doe_lcgms.name
    doe_lcgms['excluded'] = False
    doe_lcgms['pc'] = 0
    doe_lcgms['ic'] = 0
    doe_lcgms['hc'] = 0
    
    # merge doe_lcgms and sca_bluebook
    columns = ['district', 'subdistrict', 'borocode', 'bldg_name', 'excluded', 
               'bldg_id', 'org_id', 'org_level', 'name', 'address', 'pc', 'pe', 
               'ic', 'ie', 'hc', 'he', 'source','geom']
    df = sca_bluebook[columns].append(doe_lcgms[columns])
    df['geom'] = df.geom.astype('str')

    
    # export table to EDM_DATA
    exporter(df=df, 
             output_table=output_table,  
             DDL=DDL, 
             sql=f'UPDATE {output_table} SET geom=ST_SetSRID(geom,4326)')
