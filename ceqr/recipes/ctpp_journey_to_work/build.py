from ceqr.helper.engines import recipe_engine, edm_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
from pathlib import Path
import geopandas as gpd
import pandas as pd
import os

############################################################
######Part 1: generate the ctpp journy-to-work table #######
############################################################
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

    # make a list for the 31 county numbers in the scope of the project
geo_list = ['09001', '09005', '09009', '34003', '34013', '34017', 
    '34019', '34021', '34023', '34025', '34027', '34029', '34031', 
    '34035', '34037', '34039', '34041', '36005', '36027', '36047', 
    '36059', '36061', '36071', '36079', '36081', '36085', '36087', 
    '36103', '36105', '36111', '36119']


if __name__ == "__main__": 
    config = load_config(Path(__file__).parent/'config.json')
    input_table = config['inputs'][0] #ctpp_journey_to_work
    output_table = config['outputs'][0]['output_table'] #ctpp_censustract_lookup

    DDL = config['outputs'][0]['DDL']

    # load the raw dataset
    df = pd.read_sql(f'''
                    SELECT res_tract AS residential_geoid, 
                            work_tract AS work_geoid, mode, 
                            "totwork_16+" AS count, 
                            standard_error, 
                            workplace_state_county 
                    FROM {input_table}
                    ''', con=recipe_engine)

    # filter out records with workplaces outside the geo_list
    df = df[df['workplace_state_county'].isin(geo_list)]

    # map the mode field to its detailed definition
    df['mode'] = df['mode'].apply(lambda x: MODE.get(x, ''))
    df['count'] = df['count'].astype('int64')
    df['standard_error'] = df['standard_error'].astype('double')
    df['MODE'] = df['mode']

    os.system('echo "exporting table ..."')
    # export to EDM_DATA
    exporter(df, output_table, DDL, sep='|')