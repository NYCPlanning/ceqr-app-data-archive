from ceqr.helper.engines import recipe_engine, edm_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
from pathlib import Path
import os
import datetime
import pandas as pd

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
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    input_table = config['inputs'][0] # --> in this case there is only one
    output_table = config['outputs'][0]['output_table'] # --> in this case there is only one
    DDL = config['outputs'][0]['DDL']

    # ETL
    df_util = doe_util(pd.read_sql(f'select * from {input_table}', con=recipe_engine))
    df_url = pd.read_csv('output/sharepoint_urls.csv', dtype=str, index_col=False)
    df_url.fillna('', inplace=True)
    df_url['join_key'] = df_url.apply(lambda row: f"{str(row['school_year'])} {str(row['date'])}", axis=1)
    df = pd.merge(df_util, df_url, how='outer', left_on='join_key', right_on='join_key')

    # export table to EDM_DATA
    exporter(df, output_table, DDL)