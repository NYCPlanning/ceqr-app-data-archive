from ceqr.helper.engines import recipe_engine, edm_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
import datetime
import pandas as pd
from pathlib import Path
import numpy as np
import re

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

def get_cost_number(s):
    try:
        if 'e+' in s: 
            return float(s[:s.find('e')]) * 10^(float(s[-2:]))
        else:
            return float(s)
    except:
        return np.nan

def get_fund_number(s):
    try:
        return float(s)
    except:
        return np.nan
  

if __name__ == "__main__":
    # Load configuration (note: please use relative paths)
    config = load_config(Path(__file__).parent/'config.json')
    input_table = config['inputs'][0] # --> in this case there is only one
    output_table = config['outputs'][0] # --> in this case there is only one
    DDL = config['DDL']

    # import data
    df = pd.read_sql(f'select * from {input_table}', con=recipe_engine)

    # perform column transformation
    df = df[df.type.isin(['Capacity Projects', '3K Capacity Projects', 'PreK Capacity Projects'])]
    df = df.rename(columns={'projectid': 'project_dsf', 
                            'schoolname' : 'name', 
                            'geom' : 'geometry'})

    df['org_level'] = df['name'].apply(guess_org_level)
    df['capacity'] = df['forecastcapacity'].apply(get_capacity_number)
    df['pct_ps'] = df['org_level'].apply(estimate_pct_ps)
    df['pct_is'] = df['org_level'].apply(estimate_pct_is)
    df['pct_hs'] = df['org_level'].apply(estimate_pct_hs)
    df['guessed_pct'] = df['org_level'].apply(lambda x: True if x == 'PSIS' else False)
    df['start_date'] = df['constrstart'].apply(get_date)
    df['planned_end_date'] = df['actualestcompletion'].apply(get_date)
    df['total_est_cost'] = df['totalestcost'].apply(get_cost_number)
    df['funding_current_budget'] = df['fundingreqd'].apply(get_fund_number)
    df['funding_previous'] = df['previousappropriations'].apply(get_fund_number)
    df['pct_funded'] = df.apply(lambda row: (row['funding_previous']\
                                +row['funding_current_budget'])\
                                    /row['total_est_cost'], axis=1)  

    # export table to EDM_DATA
    exporter(df=df, 
            output_table=output_table, 
            con=edm_engine, 
            DDL=DDL, 
            sql=f'UPDATE {output_table} SET geometry=ST_SetSRID(ST_AsText(geometry),4326)')
