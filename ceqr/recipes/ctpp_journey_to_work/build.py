from sqlalchemy import create_engine
from pathlib import Path
import geopandas as gpd
import pandas as pd
import os
import time
import json

############################################################
######Part 1: generate the ctpp journy-to-work table #######
############################################################

def get_mode(i):
    '''
    This function is used for converting 
    mode value from coded number to its real
    definition
    '''
    MODE = {
        '1' : 'Total',
        '2' : 'Car, truck, or van -- Drove alone',
        '3' : 'Car, truck, or van -- In a 2-person carpool',
        '4' : 'Car, truck, or van -- In a 3-person carpool',
        '5' : 'Car, truck, or van -- In a 4-person carpool',
        '6' : 'Car, truck, or van -- In a 5-or-6-person carpool',
        '7' : 'Car, truck, or van -- In a 7-or-more-person carpool',
        '8' : 'Bus or trolley bus',
        '9' : 'Streetcar or trolley car',
        '10' : 'Subway or elevated',
        '11' : 'Railroad',
        '12' : 'Ferryboat',
        '13' : 'Bicycle',
        '14' : 'Walked',
        '15' : 'Taxicab',
        '16' : 'Motorcycle',
        '17' : 'Other method',
        '18' : 'Worked at home',
        }
    return MODE.get(i,'')

if __name__ == "__main__": 
    beg_ts = time.time()
    
    recipe_engine = create_engine(os.getenv('RECIPE_ENGINE'))
    edm_engine = create_engine(os.getenv('EDM_DATA'))

    config = json.loads(open(Path(__file__).parent/'config.json').read())
    input_table = config['inputs'][0]
    output_table1 = config['outputs'][0]
    output_table2 = config['outputs'][1]
    output_table_schema1 = output_table1.split('.')[0]
    output_table_schema2 = output_table2.split('.')[0]
    output_table_version1 = output_table1.split('.')[1].strip('\"')
    output_table_version2 = output_table2.split('.')[1].strip('\"')
    DDL1 = config['DDL'][output_table1]
    DDL2 = config['DDL'][output_table2]

    # load the raw dataset
    df = pd.read_sql(f'select res_tract, work_tract, mode, "totwork_16+", standard_error, workplace_state_county from {input_table}', con=recipe_engine)

    # rename column names
    df.rename(index=str, columns={'res_tract': 'residential_geoid', 
                                'work_tract': 'work_geoid',
                                'mode': 'MODE','totwork_16+': 'count',
                                'standard_error': 'standard_error' }, inplace = True)

    # make a list for the 31 county numbers in the scope of the project
    geo_list = ['09001', '09005', '09009', '34003', '34013', '34017', 
    '34019', '34021', '34023', '34025', '34027', '34029', '34031', 
    '34035', '34037', '34039', '34041', '36005', '36027', '36047', 
    '36059', '36061', '36071', '36079', '36081', '36085', '36087', 
    '36103', '36105', '36111', '36119']

    # filter out records with workplaces outside the geo_list
    df = df[df['workplace_state_county'].isin(geo_list)]

    # map the mode field to its detailed definition
    df['MODE'] = df.MODE.apply(lambda x: get_mode(x))

    # turn count and standard_error field into integer and float
    df['count']= df['count'].astype('int')
    df['standard_error']= df['standard_error'].astype('float')

    # keep the five columns included in the schema
    df = df[['residential_geoid', 'work_geoid', 'MODE', 'count', 'standard_error']]

    ############################################################
    ############ Part 2: generate the lookup table #############
    ############################################################

    # load the census tract shapefile for NY, CT and NJ
    ct_shp_09 = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/TRACT/tl_2019_09_tract.zip')
    ct_shp_34 = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/TRACT/tl_2019_34_tract.zip')
    ct_shp_36 = gpd.read_file('https://www2.census.gov/geo/tiger/TIGER2019/TRACT/tl_2019_36_tract.zip')

    # merge the 3 states shapefile together
    ct_shp = ct_shp_09.append(ct_shp_34).append(ct_shp_36)

    # calculate the centroid for each census tract
    ct_shp['centroid'] = ct_shp['geometry'].centroid

    # rename the geoid column
    ct_shp.rename(columns={'GEOID':'geoid'}, inplace=True)

    # find out the unique census tracts between residential_geoid and work_geoid
    geoid_list = pd.concat([df.residential_geoid, df.work_geoid]).unique().astype('str')

    # turn the unique census tract list into a dataframe
    geoid_df = pd.DataFrame({'geoid':geoid_list})

    # merge the journey to work census tract list with shapefile
    df_geo = pd.merge(geoid_df, ct_shp[['geoid','centroid']], on = 'geoid')

    df_geo['centroid'] = df_geo.centroid.astype('str')

    ############################################################
    ################## Part 3: dump to postgis #################
    ############################################################

    print('dumping to postgis')
    # publish to EDM_DATA
    edm_engine.connect().execute(f'CREATE SCHEMA IF NOT EXISTS {output_table_schema1}')
    df[DDL1.keys()].to_sql(output_table_version1, con = edm_engine, schema=output_table_schema1, if_exists='replace', index=False, chunksize=10000)
    
    edm_engine.connect().execute(f'CREATE SCHEMA IF NOT EXISTS {output_table_schema2}')
    edm_engine.connect().execute(f'DROP TABLE IF EXISTS {output_table2}')
    df_geo[DDL2.keys()].to_sql(output_table_version2, con = edm_engine, schema=output_table_schema2, if_exists='replace', index=False, chunksize=10000)
    edm_engine.connect().execute(f'UPDATE {output_table2} SET centroid=ST_SetSRID(centroid,4326)')

    # Change to target DDL
    for key, value in DDL1.items():
        edm_engine.connect().execute(f'ALTER TABLE {output_table1} ALTER COLUMN "{key}" TYPE {value};')

    # Change to target DDL
    for key, value in DDL2.items():
        edm_engine.connect().execute(f'ALTER TABLE {output_table2} ALTER COLUMN {key} TYPE {value};')

    end_ts = time.time()
    print(f'processing time: {(end_ts - beg_ts)/60:.3f} minutes')