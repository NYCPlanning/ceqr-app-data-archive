from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
from ceqr.helper.geocode import get_hnum, get_sname, g, GeosupportError, create_geom
from multiprocessing import Pool, cpu_count
import pandas as pd
import geopandas as gpd
from pathlib import Path
import numpy as np
import os

def geocode(inputs):
    hnum = inputs.get('house', '')
    sname = inputs.get('street', '')
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
        house_number = geo.get('House Number - Display Format', ''),
        street_name = geo.get('First Street Name Normalized', ''),
        bbl = geo.get('BOROUGH BLOCK LOT (BBL)', {}).get('BOROUGH BLOCK LOT (BBL)', '',),
        bin = geo.get('Building Identification Number (BIN) of Input Address or NAP', ''),
        latitude = geo.get('Latitude', ''),
        longitude = geo.get('Longitude', ''),
        grc = geo.get('Geosupport Return Code (GRC)', ''),        
    )

if __name__ == "__main__":
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    input_table_state = config['inputs'][0]
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']

    # import data
    df = pd.read_sql(f'''SELECT * FROM {input_table_state}''', con=recipe_engine)

    # geocoding ... with 1E
    records = df.to_dict('records')

    # Multiprocess
    with Pool(processes=cpu_count()) as pool:
        it = pool.map(geocode, records, 10000)
    
    df = pd.DataFrame(it)
    df = df[df['grc'] != '71']
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude))
    df['geometry'] = df['geometry'].apply(lambda x: None if np.isnan(x.xy[0]) else str(x))

    # export table to EDM_DATA
    exporter(df=df, 
             output_table=output_table,
             DDL=DDL)