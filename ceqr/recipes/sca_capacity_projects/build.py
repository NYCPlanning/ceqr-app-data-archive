from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter_classic
from ceqr.helper.geocode import get_hnum, get_sname, g, GeosupportError, create_geom, geo_parser
from multiprocessing import Pool, cpu_count
import datetime
import pandas as pd
import geopandas as gpd
from pathlib import Path
import numpy as np
import os
import re

def geocode(inputs):
    hnum = inputs.get('hnum', '')
    sname = inputs.get('sname', '')
    borough = inputs.get('borough', '')

    hnum = str('' if hnum is None else hnum)
    sname = str('' if sname is None else sname)
    borough = str('' if borough is None else borough)

    try:
        geo = g['1B'](street_name=sname, house_number=hnum, borough=borough)
        geo = geo_parser(geo)
        geo.update(dict(geo_function='1B'))
    except GeosupportError:
        try:
            geo = g['1B'](street_name=sname, house_number=hnum, borough=borough, mode='tpad')
            geo = geo_parser(geo)
            geo.update(dict(geo_function='1B-tpad'))
        except GeosupportError:
            try:
                geo = g['1B'](street_name=sname, house_number=hnum, borough=borough)
                geo = geo_parser(geo)
                geo.update(dict(geo_function='1B'))
            except GeosupportError as e:
                geo = e.result
                geo = geo_parser(geo)
                geo.update(dict(geo_function=''))

    geo.update(inputs)
    return geo


def clean_house(s):
    s = ' ' if s == None else s
    s = '' if s[0] == '0' else s
    s = re.sub(r"\([^)]*\)", "", s)\
        .replace(' - ', '-')\
        .split("(",maxsplit=1)[0]\
        .split("/",maxsplit=1)[0]
    return s

def clean_street(s):
    s = '' if s == None else s
    s = 'JFK INTERNATIONAL AIRPORT' if 'JFK' in s else s
    s = re.sub(r"\([^)]*\)", "", s)\
        .replace("'","")\
        .replace("VARIOUS","")\
        .replace("LOCATIONS","")\
        .split("(",maxsplit=1)[0]\
        .split("/",maxsplit=1)[0]
    return s

def parse_streetname(x, n):
    x = '' if x is None else x
    if ('&' in x)|(' AND ' in x.upper())|('CROSS' in x.upper())|('CRS' in x.upper()):
        x = re.split('&| AND | and |CROSS|CRS',x)[n]
    else: x = ''
    return x


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
        if 'P.S./I.S.' in name: return 'PSIS'
        if 'P.S.' in name: return 'PS'
        if 'I.S.' in name: return 'IS'
        if 'M.S.' in name: return 'IS'
        if 'H.S.' in name: return 'HS'
        if 'HIGH SCHOOL' in name: return 'HS'
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
    else:
        return 0

def estimate_pct_is(org_level):
    if org_level == 'IS': return 1
    elif org_level == 'PSIS': return 0.5
    else:
        return 0

def estimate_pct_hs(org_level):
    if org_level == 'HS': return 1
    else:
        return 0

def get_date(d): 
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

  
if __name__ == "__main__":
    # Load configuration (note: please use relative paths)
    config = load_config(Path(__file__).parent/'config.json')
    input_table_15_19 = config['inputs'][0] 
    input_table_20_24 = config['inputs'][1]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']

    # Import data and standardize column names
    df_15_19 = pd.read_sql(f'''
        select * from {input_table_15_19} 
        ''', con=recipe_engine).rename(columns={'DISTRICT':'district', 'SCHOOL':'name','BOROUGH':'boro',\
                                                                          'ADDRESS':'address','NUMBER OF SEATS':'forecastcapacity',\
                                                                         'OPENING & ANTICIPATED OPENING ':'estopening'})

    df_20_24 = pd.read_sql(f'''
        select * from {input_table_20_24} 
        ''', con=recipe_engine).rename(columns={'DISTRICT':'district', 'SCHOOL':'name','BOROUGH':'boro',\
                                                                          'LOCATION':'address','CAPACITY':'forecastcapacity',\
                                                                         'ANTICIPATED OPENING':'estopening'})

    # Create flag capital project plan year
    df_15_19['cap_plan'] = '15-19'
    df_20_24['cap_plan'] = '20-24'

    # Concatenate tables and flag which
    df = df_15_19.append(df_20_24, ignore_index=True)

    # Perform column transformation
    df['hnum'] = df.address.apply(get_hnum)
    df['sname'] = df.address.apply(get_sname)
    df['org_level'] = df['name'].apply(guess_org_level)
    df['capacity'] = df['forecastcapacity'].fillna(0).astype(int)
    df['pct_ps'] = df['org_level'].apply(estimate_pct_ps)
    df['pct_is'] = df['org_level'].apply(estimate_pct_is)
    df['pct_hs'] = df['org_level'].apply(estimate_pct_hs)
    df['guessed_pct'] = df['org_level'].apply(lambda x: True if x == 'PSIS' else False)

    # Geocoding
    records = df.to_dict('records')

    # Multiprocess
    with Pool(processes=cpu_count()) as pool:
        it = pool.map(geocode, records, 10000)
    
    df = pd.DataFrame(it)
    df = df[df['geo_grc'] != '71']
    df['geo_address'] = None
    df['geo_longitude'] = pd.to_numeric(df['geo_longitude'], errors='coerce')
    df['geo_latitude'] = pd.to_numeric(df['geo_latitude'], errors='coerce')
    df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.geo_longitude, df.geo_latitude))
    df['geom'] = df['geometry'].apply(lambda x: None if np.isnan(x.xy[0]) else str(x))
    df['geo_bbl'] = df.geo_bbl.apply(lambda x: None if (x == '0000000000')|(x == '') else x)

    # Export table to EDM_DATA
    exporter(df=df, 
            output_table=output_table, 
            con=edm_engine, 
            DDL=DDL)