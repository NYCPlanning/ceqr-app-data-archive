from sqlalchemy import create_engine
from pathlib import Path
import pandas as pd
import numpy as np
import math
import os
import time
import json

def get_county(c):
    '''
    This function is used for converting
    county code to county county name
    '''
    County = {
        '36061':'New York',
        '36047':'Kings' ,
        '36005':'Bronx' ,
        '36081':'Queens',
        '36085':'Richmond'
        }
    return County.get(c,'')

def get_mode(m):
    '''
    This function is used for converting 
    mode value from coded number to its real
    definition
    '''
    MODE = {
        '1': 'trans_total',
        '2': 'trans_auto_solo',
        '3': 'trans_auto_2',
        '4': 'trans_auto_3',
        '5': 'trans_auto_4',
        '6': 'trans_auto_5_or_6',
        '7': 'trans_auto_7_or_more',
        '8': 'trans_public_bus',
        '9': 'trans_public_streetcar',
        '10': 'trans_public_subway',
        '11': 'trans_public_rail',
        '12': 'trans_public_ferry',
        '13': 'trans_bicycle',
        '14': 'trans_walk',
        '15': 'trans_taxi',
        '16': 'trans_motorcycle',
        '17': 'trans_other',
        '18': 'trans_home',
        }
    
    return MODE.get(m,'')

def compute_value(total_value):
    '''
    This function is used for calculating
    the estimate value for trans_auto_carpool_total,
    trans_auto_total and trans_public_total
    '''
    total_value['trans_auto_carpool_total'] = total_value.trans_auto_2 + total_value.trans_auto_3 \
                                        + total_value.trans_auto_4 + total_value.trans_auto_5_or_6 \
                                        + total_value.trans_auto_7_or_more

    total_value['trans_auto_total'] = total_value.trans_auto_solo + total_value.trans_auto_2 \
                                + total_value.trans_auto_3 + total_value.trans_auto_4 \
                                + total_value.trans_auto_5_or_6 + total_value.trans_auto_7_or_more

    total_value['trans_public_total'] = total_value.trans_public_bus + total_value.trans_public_streetcar \
                                  + total_value.trans_public_subway + total_value.trans_public_rail \
                                  + total_value.trans_public_ferry
    total_value = total_value.melt('geoid', var_name='variable', value_name='value').sort_values(by=['geoid', 'variable'])
    
    total_value['value'] = total_value.value.astype(int)
    
    return total_value

def compute_moe(total_moe):
    '''
    This function is used for calculating
    the moe value for trans_auto_carpool_total,
    trans_auto_total and trans_public_total
    '''
    total_moe['trans_auto_carpool_total'] = total_moe.trans_auto_2**2 + total_moe.trans_auto_3**2 \
                                        + total_moe.trans_auto_4**2 + total_moe.trans_auto_5_or_6**2 \
                                        + total_moe.trans_auto_7_or_more**2

    total_moe['trans_auto_total'] = total_moe.trans_auto_solo**2 + total_moe.trans_auto_2**2 \
                                + total_moe.trans_auto_3**2 + total_moe.trans_auto_4**2 \
                                + total_moe.trans_auto_5_or_6**2 + total_moe.trans_auto_7_or_more**2

    total_moe['trans_public_total'] = total_moe.trans_public_bus**2 + total_moe.trans_public_streetcar**2 \
                                  + total_moe.trans_public_subway**2 + total_moe.trans_public_rail**2 \
                                  + total_moe.trans_public_ferry**2

    total_moe['trans_auto_carpool_total'] = total_moe.trans_auto_carpool_total.apply(lambda x: math.sqrt(x))
    total_moe['trans_auto_total'] = total_moe.trans_auto_carpool_total.apply(lambda x: math.sqrt(x))
    total_moe['trans_public_total'] = total_moe.trans_auto_carpool_total.apply(lambda x: math.sqrt(x))
    
    total_moe = total_moe.melt('geoid', var_name='variable', value_name='moe').sort_values(by=['geoid', 'variable'])
    
    total_moe['moe']= total_moe.moe.astype(int)
    
    return total_moe

def etl(data):
    '''
    This function is used for transforming
    the ctpp data to the required output
    schema
    '''
    # parse the geoid to extract the standard part
    data['geoid'] = data.geoid.apply(lambda x: x.split('US')[1][-12:])
    
    # convert value and moe to integer and float
    data['value'] = data.value.astype(int)
    data['moe'] = data.moe.astype(float)
    
    # filter the data to keep only NYC records
    nyc = ['New York', 'Kings', 'Queens', 'Bronx', 'Richmond']
    data['county'] = data.geoid.apply(lambda x:get_county(x[:-6]))
    data = data[data.county.isin(nyc)].iloc[:, :-1]
    
    # convert variable to its real definition
    data['variable'] = data.variable.apply(lambda x: get_mode(str(x)))
    
    # calculate value for trans_auto_carpool_total, trans_auto_total and trans_public_total
    total_value = data.pivot('geoid','variable','value').reset_index()
    total_value = total_value.fillna(0)
    total_value = compute_value(total_value)
    
    # calculate moe for trans_auto_carpool_total, trans_auto_total and trans_public_total
    total_moe = data.pivot('geoid','variable','moe').reset_index()
    total_moe = total_moe.fillna(0)
    total_moe = compute_moe(total_moe)
    
    # merge value table with the moe table
    data = pd.merge(total_value, total_moe, on = ['geoid', 'variable'])
    data['moe'] = data.moe.astype(int)
    data = data[['geoid', 'value', 'moe', 'variable']]
    
    return data

if __name__ == "__main__":
    beg_ts = time.time()
    
    recipe_engine = create_engine(os.getenv('RECIPE_ENGINE'))
    edm_engine = create_engine(os.getenv('EDM_DATA'))

    config = json.loads(open(Path(__file__).parent/'config.json').read())
    input_table1 = config['inputs'][1]
    input_table2 = config['inputs'][2]
    output_table1 = config['outputs'][2]
    output_table2 = config['outputs'][3]
    output_table_schema = output_table1.split('.')[0]
    output_table_version1 = output_table1.split('.')[1].strip('\"')
    output_table_version2 = output_table2.split('.')[1].strip('\"')
    DDL = config['DDL'][output_table1]

    df_2006_2010 = pd.read_sql(f'select geoid, lineno, est, se from {input_table1}', con=recipe_engine)
    df_2012_2016 = pd.read_sql(f'select geoid, lineno, est, moe from {input_table2}', con=recipe_engine)

    # rename column names
    column_names = ['geoid', 'variable', 'value', 'moe']
    df_2006_2010.columns = column_names
    df_2012_2016.columns = column_names

    # clean value and moe for df_2012_2016
    df_2012_2016['value'] = df_2012_2016.value.apply(lambda x:x.replace(',','')).astype(int)
    df_2012_2016['moe'] = df_2012_2016.moe.apply(lambda x:x[3:].replace(',',''))

    # conduct data etl
    df_2006_2010 = etl(df_2006_2010)
    df_2012_2016 = etl(df_2012_2016)

    print('dumping to postgis')
    # publish to EDM_DATA
    edm_engine.connect().execute(f'CREATE SCHEMA IF NOT EXISTS {output_table_schema}')
    df_2006_2010[DDL.keys()].to_sql(output_table_version1, con = edm_engine, schema=output_table_schema, if_exists='replace', index=False, chunksize=10000)
    df_2012_2016[DDL.keys()].to_sql(output_table_version2, con = edm_engine, schema=output_table_schema, if_exists='replace', index=False, chunksize=10000)

    # Change to target DDL
    for key, value in DDL.items():
        edm_engine.connect().execute(f'ALTER TABLE {output_table1} ALTER COLUMN {key} TYPE {value};')
        edm_engine.connect().execute(f'ALTER TABLE {output_table2} ALTER COLUMN {key} TYPE {value};')
    end_ts = time.time()
    print(f'processing time: {(end_ts - beg_ts):.3f} seconds')