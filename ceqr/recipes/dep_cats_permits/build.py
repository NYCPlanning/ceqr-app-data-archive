from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter_classic
from ceqr.helper.geocode import get_hnum, get_sname, g, GeosupportError, create_geom, geo_parser
from multiprocessing import Pool, cpu_count
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
    street_name_1 = inputs.get('streetname_1', '')
    street_name_2 = inputs.get('streetname_2', '')

    hnum = str('' if hnum is None else hnum)
    sname = str('' if sname is None else sname)
    borough = str('' if borough is None else borough)
    street_name_1 = str('' if street_name_1 is None else street_name_1)
    street_name_2 = str('' if street_name_2 is None else street_name_2)

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
                if street_name_1 != '':
                    geo = g['2'](street_name_1=street_name_1, street_name_2=street_name_2, borough_code=borough)
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

def parse_streetname(x, n):
    x = '' if x is None else x
    if ('&' in x)|(' AND ' in x.upper())|('CROSS' in x.upper())|('CRS' in x.upper()):
        x = re.split('&| AND | and |CROSS|CRS',x)[n]
    else: x = ''
    return x

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
    df['hnum'] = df.housenum.apply(lambda x: clean_house(x))
    df['sname'] = df.streetname.apply(lambda x: clean_street(x))
    df['address'] = df.hnum + ' ' + df.sname
    df['hnum'] = df.address.apply(get_hnum)
    df['sname'] = df.address.apply(get_sname)

    df['streetname_1'] = df['address'].apply(lambda x: parse_streetname(x, 0)).apply(get_sname)
    df['streetname_2'] = df['address'].apply(lambda x: parse_streetname(x, -1)).apply(get_sname)
    df['status'] = df['status'].apply(lambda x: x.strip())
    # geocoding
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
            UPDATE {output_table} SET geom = (CASE
                                            WHEN geo_function = 'Intersection'
                                            THEN ST_TRANSFORM(ST_SetSRID(ST_MakePoint(geo_x_coord::NUMERIC,geo_y_coord::NUMERIC),2263),4326)::TEXT
                                            ELSE geom
                                        END),
                                    geo_x_coord = (CASE
                                                    WHEN geo_x_coord = ''
                                                    THEN NULL
                                                    ELSE geo_x_coord
                                                END),
                                    geo_y_coord = (CASE
                                                    WHEN geo_y_coord = ''
                                                    THEN NULL
                                                    ELSE geo_y_coord
                                                END);
            DELETE FROM {output_table}
            WHERE geom IS NULL;
            '''

    SQL2 = f'''
            UPDATE {output_table2} SET geom=ST_SetSRID(geom,4326),
                                       geo_address=geo_housenum||' '||geo_streetname;
            UPDATE {output_table2} SET geom = (CASE
                                        WHEN geo_function = 'Intersection'
                                        THEN ST_TRANSFORM(ST_SetSRID(ST_MakePoint(geo_x_coord::NUMERIC,geo_y_coord::NUMERIC),2263),4326)::TEXT
                                        ELSE geom
                                    END),
                                geo_x_coord = (CASE
                                                WHEN geo_x_coord = ''
                                                THEN NULL
                                                ELSE geo_x_coord
                                            END),
                                geo_y_coord = (CASE
                                                WHEN geo_y_coord = ''
                                                THEN NULL
                                                ELSE geo_y_coord
                                            END);
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