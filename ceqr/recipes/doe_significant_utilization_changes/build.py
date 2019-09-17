from pathlib import Path
from sqlalchemy import create_engine
import os
import datetime
import pandas as pd
import json

def doe_util(df):
    def get_date(d):
        try: 
            d = datetime.datetime.strptime(d,'%m/%d/%Y')
            d = d.date()
            if d < datetime.date(2016, 4, 21):
                d = ''
            else: 
                d = d.isoformat()
            return str(d)
        except: 
            return ''

    def get_school_year(d):
        try: 
            d = datetime.datetime.strptime(d,'%m/%d/%Y')
            y = d.year
            if d.month < 9:
                return f'{y-1}-{y}'
            else: 
                return f'{y}-{y+1}'
        except: 
            return ''

    def format_date(d):
        try: 
            d = datetime.datetime.strptime(d,'%Y-%m-%dT%H:%M:%S')
            d = d.date()
            return d.strftime('%m/%d/%Y')
        except:
            return ''

    def get_at_scale_enroll(e): 
        try:
            e = e.replace('–','-').split('-')[-1]
            return int(e)
        except: 
            return 0

    df = df[df['approved'] == 'Approved']
    df = df.rename(
        columns={
            'main_building_id': 'bldg_id', 
            'other_impacted_building' : 'bldg_id_additional', 
            'proposal_title':'title', 'at_scale_year':'at_scale_year'})
    df['org_id'] = df['dbn'].apply(lambda x: x[-4:])
    df['at_scale_enroll'] = df['at_scale_school_enrollment'].apply(get_at_scale_enroll)
    df['vote_date'] = df['pep_vote']
    df['date_tmp'] = df['pep_vote'].apply(get_date)
    df['school_year'] = df['pep_vote'].apply(get_school_year)
    df['join_key'] = df.apply(lambda row: f"{row['school_year']} {row['date_tmp']}", axis=1)
    return df

if __name__ == "__main__":    
    recipe_engine = create_engine(os.getenv('RECIPE_ENGINE'))
    edm_engine = create_engine(os.getenv('EDM_DATA'))

    # Load configuration
    config = json.loads(open(Path(__file__).parent/'config.json').read())
    input_table = config['inputs'][0] # --> in this case there is only one
    output_table = config['outputs'][0] # --> in this case there is only one
    output_table_schema = output_table.split('.')[0]
    output_table_version = output_table.split('.')[1]
    DDL = config['DDL']

    # import data
    df_util = doe_util(pd.read_sql(f'select * from {input_table}', con=recipe_engine))

    df_url = pd.read_csv('output/sharepoint_urls.csv', dtype=str, index_col=False)
    df_url.fillna('', inplace=True)
    df_url['join_key'] = df_url.apply(lambda row: f"{str(row['school_year'])} {str(row['date'])}", axis=1)

    df = pd.merge(df_util, df_url, how='outer', left_on='join_key', right_on='join_key')

     # publish to EDM_DATA
    edm_engine.connect().execute(f'CREATE SCHEMA IF NOT EXISTS {output_table_schema}')
    df[DDL.keys()].to_sql(output_table_version,
                            con = edm_engine,
                            schema=output_table_schema,
                            if_exists='replace',
                            index=False)
                            
    # Change to target DDL
    for key, value in DDL.items():
        edm_engine.connect().execute(f'ALTER TABLE {output_table} ALTER COLUMN {key} TYPE {value};')