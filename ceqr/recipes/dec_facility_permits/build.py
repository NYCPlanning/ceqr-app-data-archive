from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
from ceqr.helper.geocode import get_hnum, get_sname, g, GeosupportError, create_geom
from multiprocessing import Pool, cpu_count
from shapely.wkt import loads, dumps
import pandas as pd
import geopandas as gpd
from pathlib import Path
import numpy as np
import os

def geocode(inputs):
    hnum = inputs.pop('hnum')
    sname = inputs.pop('sname')
    zip_code = inputs.pop('zip_code')

    hnum = str('' if hnum is None else hnum)
    sname = str('' if sname is None else sname)
    zip_code = str('' if zip_code is None else zip_code)
    try: 
        geo = g['1B'](street_name=sname, house_number=hnum, zip_code=zip_code)
    except GeosupportError as e:
        geo = e.result
    
    geo = parser(geo)
    geo.update(inputs)
    return geo

def parser(geo):
    return dict(
        house_number = geo.get('House Number - Display Format', ''),
        street_name = geo.get('First Street Name Normalized', ''),
        bbl = geo.get('BOROUGH BLOCK LOT (BBL)', {}).get('BOROUGH BLOCK LOT (BBL)', '',),
        bin = geo.get('Building Identification Number (BIN) of Input Address or NAP', ''),
        latitude = geo.get('Latitude', ''),
        longitude = geo.get('Longitude', ''),
        grc = geo.get('Geosupport Return Code (GRC)', ''),        
    )
def test(a):
    return {'a':'1', 'b':'2'}

if __name__ == "__main__":
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    input_table_state = config['inputs'][0]
    input_table_title_v = config['inputs'][1]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']

    # import data
    dec_state_facility_permits = pd.read_sql(f'''SELECT *, 'State' AS source FROM {input_table_state}''', con=recipe_engine)
    dec_title_v_facility_permits = pd.read_sql(f'''SELECT *, 'Title V' AS source FROM {input_table_title_v}''', con=recipe_engine)

    dec_title_v_facility_permits.columns = dec_state_facility_permits.columns

    df = dec_state_facility_permits.append(dec_title_v_facility_permits)

    # geocoding ... with 1E
    df['hnum'] = df['facility_location'].apply(get_hnum)
    df['sname'] = df['facility_location'].apply(get_sname)
    df['zip_code'] = df['facility_zip']
    records = df.to_dict('records')

    # Multiprocess
    with Pool(processes=cpu_count()) as pool:
        it = pool.map(geocode, records, 10000)
    
    df = pd.DataFrame(it)
    df = df[df['grc'] != '71']

    df['longitude'] = pd.to_numeric(df['longitude'],errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'],errors='coerce')
    df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    df['geometry'] = df['geometry'].apply(lambda x: None if np.isnan(x.xy[0]) else str(x))

    SQL = f'''
        ALTER TABLE dec_facility_permits.latest 
        ADD COLUMN id SERIAL PRIMARY KEY;

        DELETE FROM {output_table}
        WHERE id NOT IN(
            WITH date AS(
                SELECT facility_name||facility_location AS facility, MAX(issue_date::date) as latest_issue_date
                FROM {output_table}
                GROUP BY facility_name||facility_location
            )
            SELECT min(id)
            FROM {output_table} p, date d
            WHERE p.facility_name||facility_location = d.facility
            AND p.issue_date::date = d.latest_issue_date
            OR d.latest_issue_date IS NULL
            GROUP BY p.facility_name||facility_location
        );

        ALTER TABLE dec_facility_permits.latest DROP COLUMN id;

        UPDATE {output_table} SET geometry=ST_SetSRID(geometry,4326); 
        '''

    os.system('echo "exporting table ..."')
    # export table to EDM_DATA
    exporter(df=df, 
             output_table=output_table,  
             DDL=DDL,
             sql=SQL)