from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
from ceqr.helper.geocode import get_hnum, get_sname, g, GeosupportError, create_geom, geo_parser
from multiprocessing import Pool, cpu_count
import datetime
import pandas as pd
import geopandas as gpd
from pathlib import Path
import numpy as np
import os
import re


def clean_house(s):
    s = ' ' if s == None else s
    s = re.sub(r"\([^)]*\)", "", s)\
        .replace(' - ', '-')\
        .strip()\
        .split("(",maxsplit=1)[0]\
        .split("/",maxsplit=1)[0]
    return s

def clean_street(s):
    s = '' if s == None else s
    s = re.sub(r"\([^)]*\)", "", s)\
        .replace("'","")\
        .split("(",maxsplit=1)[0]\
        .split("/",maxsplit=1)[0]
    return s

def find_stretch(address):
    if 'BETWEEN' in address:
        street_1 = address.split('BETWEEN')[0].strip()
        street_2 = (address.split('BETWEEN')[1].split('AND')[0] + address.split(' ')[-1]).strip()
        street_3 = address.split('BETWEEN')[1].split('AND')[1].strip()
        return street_1, street_2, street_3
    else:
        return '','',''
    
def find_intersection(address):
    if 'AND' in address:
        street_1 = address.split('AND')[0].strip()
        street_2 = address.split('AND')[1].strip()
        return street_1, street_2
    else:
        return '',''

def geocode(inputs):
    hnum = inputs.get('hnum', '')
    sname = inputs.get('sname', '')
    borough = inputs.get('borough', '')

    hnum = str('' if hnum is None else hnum)
    sname = str('' if sname is None else sname)
    borough = str('' if borough is None else borough)
  
    try:
        # First try to geocode using 1B
        geo = g['1B'](street_name=sname, house_number=hnum, borough=borough)
        geo = geo_parser(geo)
        geo.update(geo_function='1B')
    except GeosupportError:
        # Try to parse original address as a stretch
        try:
            street_1, street_2, street_3 = find_stretch(inputs.get('address'))
            if (street_1 != '')&(street_2 != '')&(street_3 != ''):
                # Call to geosupport function 3
                geo = g['3'](street_name_1=street_1, street_name_2=street_2, street_name_3=street_3, borough_code=borough)
                geo_from_node = geo.get('From Node', '')
                geo_to_node = geo.get('To Node', '')
                geo_from_x_coord = g['2'](node=geo_from_node).get('SPATIAL COORDINATES', {}).get('X Coordinate', '')
                geo_from_y_coord = g['2'](node=geo_from_node).get('SPATIAL COORDINATES', {}).get('Y Coordinate', '')
                geo_to_x_coord = g['2'](node=geo_to_node).get('SPATIAL COORDINATES', {}).get('X Coordinate', '')
                geo_to_y_coord = g['2'](node=geo_to_node).get('SPATIAL COORDINATES', {}).get('Y Coordinate', '')
                geo.update(dict(geo_from_x_coord=geo_from_x_coord, geo_from_y_coord=geo_from_y_coord, geo_to_x_coord=geo_to_x_coord, geo_to_y_coord=geo_to_y_coord, geo_function='Segment'))
            else:
                geo = g['1B'](street_name=sname, house_number=hnum, borough=borough)
                geo = geo_parser(geo)
                geo.update(dict(geo_function='1B'))
        except:
            try:
                # Try to parse original address as an intersection
                street_1, street_2 = find_intersection(inputs.get('address'))
                if (street_1 != '')&(street_2 != ''):
                    # Call to geosupport function 2
                    geo = g['2'](street_name_1=street_1, street_name_2=street_2, borough_code=borough)
                    geo = geo_parser(geo)
                    geo.update(dict(geo_function='Intersection'))
                else:
                    geo = g['1B'](street_name=sname, house_number=hnum, borough=borough)
                    geo = geo_parser(geo)
                    geo.update(dict(geo_function='1B'))
            except GeosupportError as e:
                geo = e.result
                geo = geo_parser(geo)
                geo.update(dict(geo_function=''))

    geo.update(inputs)
    return geo

def get_date(d): 
    try:
        d = datetime.datetime.strptime(d,'%B %Y')\
            .strftime('%Y-%m-%d %H:%M:%S+00')
        return str(d)
    except:
        pass
    try:
        d = datetime.datetime.strptime(d,'%b-%y')\
            .strftime('%Y-%m-%d %H:%M:%S+00')
        return str(d)
    except:
        pass
    try:
        d = datetime.datetime.strptime(d,'%y-%b')\
            .strftime('%Y-%m-%d %H:%M:%S+00')
        return str(d)
    except:
        pass
    try:
        d = datetime.datetime.strptime(d,'%Y-%m-%d %H:%M:%S0')\
            .strftime('%Y-%m-%d %H:%M:%S+00')
        return str(d)
    except:
        return ''

def guess_org_level(name):
    '''
    This function is used to 
    make a guess at the school
    organization level based on
    its school name
    '''
    try: # P.S, M.S, H.S etc will be identified
        if '3K' in name: return '3K'
        if 'PRE-K' in name: return "PK"
        if 'P.S./I.S.' in name.replace(" ", ""): return 'PSIS'
        if 'I.S./H.S.' in name.replace(" ", ""): return 'ISHS'
        if 'P.S./H.S.' in name.replace(" ", ""): return 'PSHS'
        if 'P.S.' in name: return 'PS'
        if 'I.S.' in name: return 'IS'
        if 'M.S.' in name: return 'IS'
        if 'H.S.' in name: return 'HS'
        if 'HIGH SCHOOL' in name: return 'HS'
        if 'D75' in name: return 'SE'
    except:
        pass
    try: # PS, IS, HS will be identified
        if re.search(r'\bPS\b', name) != None: return 'PS' 
        if re.search(r'\bIS\b', name) != None: return 'IS'
        if re.search(r'\bHS\b', name) != None: return 'HS' 
    except:
        return np.nan

def get_capacity_number(s):
    s = s.strip()
    try:
        s = int(s)
        return s
    except:
        return np.nan

def estimate_pct_ps(org_level):
    '''
    PS org_level make pct_ps = 1, everything else 0
    PSIS org_level makes pct_ps = 0.5, pct_is = 0.5
    etc. etc.
    3K and PRE-K doesn’t set anything
    '''
    if org_level == 'PS': return 1
    elif org_level == 'PSIS': return 0.5
    elif org_level == 'PSHS': return 0.5
    else:
        return 0

def estimate_pct_is(org_level):
    if org_level == 'IS': return 1
    elif org_level == 'PSIS': return 0.5
    elif org_level == 'ISHS': return 0.5
    else:
        return 0

def estimate_pct_hs(org_level):
    if org_level == 'HS': return 1
    elif org_level == 'PSHS': return 0.5
    elif org_level == 'ISHS': return 0.5
    else:
        return 0

def get_boro(b):
    BORO = dict(
        M = 'Manhattan',
        X = 'Bronx',
        K = 'Brooklyn',
        Q = 'Queens',
        R = 'Staten Island',
    )
    return BORO.get(b.strip(), '')

def get_sql(output_table, output_table_schema):
    SQL = f'''
        ALTER TABLE {output_table}
        ADD geo_from_geom GEOMETRY,
        ADD geo_to_geom GEOMETRY;
        UPDATE {output_table}
        SET geo_from_geom = ST_TRANSFORM(ST_SetSRID(ST_MakePoint(geo_from_x_coord::NUMERIC,
                                                                 geo_from_y_coord::NUMERIC),2263),4326),
            geo_to_geom = ST_TRANSFORM(ST_SetSRID(ST_MakePoint(geo_to_x_coord::NUMERIC,
                                                               geo_to_y_coord::NUMERIC),2263),4326)
        WHERE geo_function = 'Segment';

        UPDATE {output_table} SET geom = (CASE
                                            WHEN geo_function = 'Intersection'
                                                THEN ST_TRANSFORM(ST_SetSRID(ST_MakePoint(geo_x_coord,geo_y_coord),2263),4326)
                                            WHEN geo_function = 'Segment'
                                                THEN ST_centroid(ST_MakeLine(geo_from_geom, geo_to_geom))
                                            ELSE geom
                                        END);

        UPDATE {output_table} SET geo_function = '1E',
                                  geom = ST_TRANSFORM(ST_SetSRID(ST_MakePoint(LEFT(geo_xy_coord, 7)::DOUBLE PRECISION,\
                                                                              RIGHT(geo_xy_coord, 7)::DOUBLE PRECISION),2263),4326)
        WHERE geo_function = '1B'\
        AND geom IS NULL\
        AND geo_xy_coord IS NOT NULL;

        ALTER TABLE {output_table}
        DROP COLUMN geo_xy_coord,
        DROP COLUMN geo_x_coord,
        DROP COLUMN geo_y_coord,
        DROP COLUMN geo_from_x_coord,
        DROP COLUMN geo_from_y_coord,
        DROP COLUMN geo_to_x_coord,
        DROP COLUMN geo_to_y_coord,
        DROP COLUMN geo_from_geom,
        DROP COLUMN geo_to_geom;

        DROP TABLE IF EXISTS {output_table_schema}.geo_rejects;
        SELECT * INTO {output_table_schema}.geo_rejects
        FROM {output_table}
        WHERE geom IS NULL;

        DELETE FROM {output_table}
        WHERE geom IS NULL;

        ALTER TABLE {output_table}
        DROP COLUMN geo_grc,
        DROP COLUMN geo_grc2,
        DROP COLUMN geo_reason_code,
        DROP COLUMN geo_message;
        '''
    return SQL
  
if __name__ == "__main__":
    # Load configuration (note: please use relative paths)
    config = load_config(Path(__file__).parent/'config.json')
    input_table_15_19 = config['inputs'][0] 
    input_table_20_24 = config['inputs'][1]

    # Primary output table
    output_table = config['outputs'][0]['output_table']
    output_table_schema = config['outputs'][0]['output_table'].split('.')[0]
    DDL = config['outputs'][0]['DDL']

    # Unfiltered output table
    output_table_all = config['outputs'][1]['output_table']
    output_table_schema_all = config['outputs'][1]['output_table'].split('.')[0]
    DDL_all = config['outputs'][1]['DDL']

    # Import data and standardize column names
    df_15_19 = pd.read_sql(f'''
        select * from {input_table_15_19} 
        ''', con=recipe_engine).rename(columns={'school':'name',\
                                                'number_of_seats':'forecastcapacity',\
                                                'opening_&_anticipated_opening':'start_date'})

    df_20_24 = pd.read_sql(f'''
        select * from {input_table_20_24} 
        ''', con=recipe_engine).rename(columns={'school':'name',\
                                                'location':'address','capacity':'forecastcapacity',\
                                                'anticipated_opening':'start_date'})

    # Create flag capital project plan year
    df_15_19['capital_plan'] = '15-19'
    df_20_24['capital_plan'] = '20-24'

    # Concatenate tables
    df = df_15_19.append(df_20_24, ignore_index=True)

    # Import csv to replace invalid addresses with manual corrections
    cor_add_dict = pd.read_csv('https://raw.githubusercontent.com/NYCPlanning/ceqr-app-data/master/ceqr/data/sca_capacity_address_cor.csv').to_dict('records')
    for record in cor_add_dict:
        df.loc[df['name']==record['school'],'address'] = record['address'].upper()

    # Perform column transformation
    df['borough'] = df['borough'].apply(get_boro)
    df['hnum'] = df.address.apply(get_hnum).apply(lambda x: clean_house(x))
    df['sname'] = df.address.apply(get_sname).apply(lambda x: clean_street(x))
    df['org_level'] = df['name'].apply(guess_org_level)

    # Import csv to replace org_levels with manual corrections
    cor_org_dict = pd.read_csv('https://raw.githubusercontent.com/NYCPlanning/ceqr-app-data/master/ceqr/data/sca_capacity_org_level_cor.csv').to_dict('records')
    for record in cor_org_dict:
        df.loc[df['name']==record['school'],'org_level'] = record['org_level']

    df['capacity'] = df['forecastcapacity'].fillna(0).astype(int)
    df['start_date'] = df['start_date'].apply(get_date)
    df['pct_ps'] = df['org_level'].apply(estimate_pct_ps)
    df['pct_is'] = df['org_level'].apply(estimate_pct_is)
    df['pct_hs'] = df['org_level'].apply(estimate_pct_hs)
    df['guessed_pct'] = df['org_level'].apply(lambda x: True if len(x) > 2 else False)

    # Set special education org level to Null
    df.loc[df['org_level'] == 'SE','org_level'] = np.nan

    # Geocoding 1B, intersection, segment
    records = df.to_dict('records')

    # Multiprocess
    with Pool(processes=cpu_count()) as pool:
        it = pool.map(geocode, records, 10000)
    
    df = pd.DataFrame(it)

    df['geo_longitude'] = pd.to_numeric(df['geo_longitude'], errors='coerce')
    df['geo_latitude'] = pd.to_numeric(df['geo_latitude'], errors='coerce')
    df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.geo_longitude, df.geo_latitude))
    df['geom'] = df['geometry'].apply(lambda x: None if np.isnan(x.xy[0]) else str(x))

    geo_rejects = df[(df['geom'].isnull())&(df['geo_x_coord']=='')&(df['geo_from_x_coord'].isnull())&(df['geo_xy_coord']=='')]
    print('Percent of records geocoded: ', (len(df)-len(geo_rejects))/len(df))

    # Export unfiltered table to EDM_DATA
    exporter(df=df, 
            output_table=output_table_all, 
            con=edm_engine,
            geo_column='geom', 
            DDL=DDL,
            sql=get_sql(output_table_all, output_table_schema_all))

    # Remove special ed cases
    df_filtered = df[(df['district']!='75')&(df.org_level!='PK')&(df.org_level!='3K')]

    # Export filtered table to EDM_DATA
    exporter(df=df_filtered, 
            output_table=output_table, 
            con=edm_engine,
            geo_column='geom', 
            DDL=DDL,
            sql=get_sql(output_table, output_table_schema))