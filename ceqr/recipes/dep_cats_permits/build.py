from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter_classic
from ceqr.helper.geocode import get_hnum, get_sname, g, GeosupportError, create_geom
from multiprocessing import Pool, cpu_count
import pandas as pd
import geopandas as gpd
from pathlib import Path
import numpy as np
import os
import re

def geocode(inputs):
    hnum = inputs.get('clean_housenum', '')
    sname = inputs.get('clean_streetname', '')
    borough = inputs.get('borough', '')

    hnum = str('' if hnum is None else hnum)
    sname = str('' if sname is None else sname)
    borough = str('' if borough is None else borough)
    try: 
        geo = g['1B'](street_name=sname, house_number=hnum, borough=borough)
    except GeosupportError as e:
        geo = e.result
    
    geo = parser(geo)
    geo.update(inputs)
    return geo

def parser(geo): 
    return dict(
        geo_housenum = geo.get('House Number - Display Format', ''),
        geo_streetname = geo.get('First Street Name Normalized', ''),
        geo_bbl = geo.get('BOROUGH BLOCK LOT (BBL)', {}).get('BOROUGH BLOCK LOT (BBL)', '',),
        geo_bin = geo.get('Building Identification Number (BIN) of Input Address or NAP', ''),
        geo_latitude = geo.get('Latitude', ''),
        geo_longitude = geo.get('Longitude', ''),
        geo_grc = geo.get('Geosupport Return Code (GRC)', ''),
        geo_message = geo.get('Message', 'msg err')
    )

def clean_boro(b):
    if b == 'STATENISLAND':
        b = 'STATEN ISLAND'
    if b not in ['BRONX', 'MANHATTAN', 'BROOKLYN', 'QUEENS', 'STATEN ISLAND']:
        b = None
    if b != None: 
        b = b.title()
    return b

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

if __name__ == "__main__":
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    input_table = config['inputs'][0]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']
    output_table2 = config['outputs'][1]['output_table']
    DDL2 = config['outputs'][1]['DDL']

    # import data
    df = pd.read_sql(f'SELECT * FROM {input_table}', con=recipe_engine)
    df.rename(columns={"house": "housenum", "street": "streetname",
                       "issuedate": "issue_date", "expirationdate": 'expiration_date'}, inplace=True)
    df['borough'] = df.borough.apply(lambda x: clean_boro(x))
    df['borough'] = np.where((df.streetname.str.contains('JFK'))&(df.borough == None),'Queens',df.borough)
    df['clean_housenum'] = df.housenum.apply(lambda x: clean_house(x))
    df['clean_streetname'] = df.streetname.apply(lambda x: clean_street(x))
    df['address'] = df.clean_housenum + ' ' + df.clean_streetname
    df['clean_housenum'] = df.address.apply(get_hnum)
    df['clean_streetname'] = df.address.apply(get_sname)
    # geocoding ... with 1E
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

    SQL = f'''
            UPDATE {output_table} SET geom=ST_SetSRID(geom,4326),
                                      geo_address=geo_housenum||' '||geo_streetname;
            DELETE FROM {output_table}
            WHERE geom IS NULL;
            '''

    SQL2 = f'''
            UPDATE {output_table2} SET geom=ST_SetSRID(geom,4326),
                                       geo_address=geo_housenum||' '||geo_streetname;
            DELETE FROM {output_table2}
            WHERE geom IS NOT NULL;
            '''
    # export table to EDM_DATA
    exporter_classic(df=df,
            output_table=output_table,
            DDL=DDL,
            sql=SQL)

    # export table to EDM_DATA
    exporter_classic(df=df,
            output_table=output_table2,
            DDL=DDL2,
            sql=SQL2)