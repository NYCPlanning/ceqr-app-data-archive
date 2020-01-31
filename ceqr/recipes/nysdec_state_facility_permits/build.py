from ceqr.helper.geocode import get_hnum, get_sname, g, GeosupportError, create_geom, geo_parser
from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
from multiprocessing import Pool, cpu_count
import pandas as pd
import geopandas as gpd
from pathlib import Path
import numpy as np
import os
import re

def geocode(inputs):
    hnum = inputs.get('housenum', '')
    sname = inputs.get('streetname', '')
    zip_code = inputs.get('zipcode', '')
    borough_code = inputs.get('borough', '')
    street_name_1 = inputs.get('streetname_1', '')
    street_name_2 = inputs.get('streetname_2', '')

    hnum = str('' if hnum is None else hnum)
    sname = str('' if sname is None else sname)
    zip_code = str('' if zip_code is None else zip_code)
    borough_code = str('' if borough_code is None else borough_code)
    street_name_1 = str('' if street_name_1 is None else street_name_1)
    street_name_2 = str('' if street_name_2 is None else street_name_2)

    try:
        geo = g['1B'](street_name=sname, house_number=hnum, zip_code=zip_code)
        geo = geo_parser(geo)
        geo.update(dict(geo_function='1B'))
    except GeosupportError:
        try:
            geo = g['1B'](street_name=sname, house_number=hnum, zip_code=zip_code, mode='tpad')
            geo = geo_parser(geo)
            geo.update(dict(geo_function='1B-tpad'))
        except GeosupportError:
            try:
                geo = g['AP'](street_name=sname, house_number=hnum, zip_code=zip_code)
                geo = geo_parser(geo)
                geo.update(dict(geo_function='AP'))
            except GeosupportError:
                try:
                    if street_name_1 != '':
                        geo = g['2'](street_name_1=street_name_1, street_name_2=street_name_2, borough_code=borough_code)
                        geo = geo_parser(geo)
                        geo.update(dict(geo_function='Intersection'))
                    else:
                        geo = g['1B'](street_name=sname, house_number=hnum, zip_code=zip_code)
                        geo = geo_parser(geo)
                        geo.update(dict(geo_function='1B'))
                except GeosupportError as e:
                    geo = e.result
                    geo = geo_parser(geo)
                    geo.update(dict(geo_function=''))

    geo.update(inputs)
    return geo

def clean_address(x):
    x = '' if x is None else x
    sep = ['|', '&', '@', ' AND ']
    for i in sep:
        x = x.split(i, maxsplit=1)[0]
    return x

def clean_streetname(x, n):
    x = '' if x is None else x
    if ('&' in x)|(' AND ' in x.upper()):
        x = re.split('&| AND | and ',x)[n]
    else: x = ''
    return x

if __name__ == "__main__":
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    input_table = config['inputs'][0]
    input_table_nyc = config['inputs'][1]
    input_table_boro = config['inputs'][2]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']
    output_table_schema = config['outputs'][0]['output_table'].split('.')[0]

    # import data
    df = pd.read_sql(f'''SELECT * FROM {input_table}''', con=recipe_engine)
    nyc = pd.read_sql(f'''SELECT zipcode, UPPER(city) AS city FROM {input_table_nyc}''', con=recipe_engine)
    zip_boro = pd.read_sql(f'''SELECT zipcode, borough FROM {input_table_boro}''', con=recipe_engine)
    corr = pd.read_csv('https://raw.githubusercontent.com/NYCPlanning/ceqr-app-data/master/ceqr/data/ceqr_input_research.csv')

    # rename column names
    df.rename(columns={"facility_zip": "zipcode", "expire_date": "expiration_date"}, inplace=True)
    corr.rename(columns={"id": "permit_id", "location": "facility_location", "city": "facility_city"}, inplace=True)
    corr = corr[corr.datasource==output_table_schema].drop(columns='datasource')

    # fill boroughs, update location based on ceqr_input_research
    df['permit_id'] = df['permit_id'].apply(lambda x: x.strip() if x!=None else x)
    df['facility_city'] = df['facility_city'].apply(lambda x: x.upper() if x!=None else x)
    df = pd.merge(df, zip_boro, how = 'left', on = 'zipcode')
    df = pd.merge(df, corr, how = 'left', on =['permit_id','facility_location', 'facility_city'])
    df.fillna({'correction':'', 'longitude':'', 'latitude':''}, inplace = True)

    # filter out cities or zipcode outside NYC
    df['facility_city'] = df.facility_city.apply(lambda x: x.upper() if x != None else '')
    df = df[(df.facility_city.isin(nyc.city.values))|(df.zipcode.isin(nyc.zipcode.values))|
                    (df.facility_city == '')|(df.zipcode == '')]

    # generate inputs for geocoding
    df['address'] = df['facility_location'].apply(lambda x: clean_address(x))
    df['address'] = np.where(df.correction!='',df.correction,df.address) # correct the locations in ceqr_input_research
    df['housenum'] = df['address'].apply(get_hnum)\
                                  .apply(lambda x: x.split('/',maxsplit=1)[0] if x != None else x)
    df['streetname'] = df['address'].apply(get_sname)
    df['streetname_1'] = df['facility_location'].apply(lambda x: clean_streetname(x, 0)).apply(get_sname)
    df['streetname_2'] = df['facility_location'].apply(lambda x: clean_streetname(x, -1)).apply(get_sname)

    records = df.to_dict('records')

    # geocoding
    with Pool(processes=cpu_count()) as pool:
        it = pool.map(geocode, records, 10000)
    df = pd.DataFrame(it)
    df = df[df['geo_grc'] != '71']

    # fill lat, lon based on ceqr_input_research
    df['geo_function'] = np.where((df.longitude!='')&(df.geo_x_coord=='')&(df.geo_longitude==''),'DCP_Manual',df.geo_function)
    df['geo_longitude'] = np.where(df.geo_function=='DCP_Manual',df.longitude,df.geo_longitude)
    df['geo_latitude'] = np.where(df.geo_function=='DCP_Manual',df.latitude,df.geo_latitude)

    # generate geom
    df['geo_address'] = None
    df['geo_longitude'] = pd.to_numeric(df['geo_longitude'],errors='coerce')
    df['geo_latitude'] = pd.to_numeric(df['geo_latitude'],errors='coerce')
    df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.geo_longitude, df.geo_latitude))
    df['geom'] = df['geometry'].apply(lambda x: None if np.isnan(x.xy[0]) else str(x))

    # remove geo_lat and geo_lon for manual research
    df['geo_longitude'] = np.where(df.geo_function=='DCP_Manual',None,df.geo_longitude)
    df['geo_latitude'] = np.where(df.geo_function=='DCP_Manual',None,df.geo_latitude)

    SQL = f'''
        UPDATE {output_table} SET geo_address=geo_housenum||' '||geo_streetname,
                                  geom = (CASE
                                            WHEN geo_function = 'Intersection'
                                            THEN ST_TRANSFORM(ST_SetSRID(ST_MakePoint(geo_x_coord,geo_y_coord),2263),4326)
                                            ELSE geom
                                        END);

        ALTER TABLE {output_table}
        ADD COLUMN id SERIAL PRIMARY KEY;

        DELETE FROM {output_table}
        WHERE id NOT IN(
            WITH date AS(
                SELECT facility_name||address AS facility, MAX(issue_date::date) as latest_issue_date
                FROM {output_table}
                GROUP BY facility_name||address
            )
            SELECT min(id)
            FROM {output_table} p, date d
            WHERE p.facility_name||address = d.facility
            AND p.issue_date::date = d.latest_issue_date
            OR d.latest_issue_date IS NULL
            GROUP BY p.facility_name||address
        )
        ;

        ALTER TABLE {output_table} DROP COLUMN id;

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

    os.system('echo "exporting table ..."')
    # export table to EDM_DATA
    exporter(df=df,
             output_table=output_table,
             DDL=DDL,
             sql=SQL,
             sep='~',
             geo_column='geom')