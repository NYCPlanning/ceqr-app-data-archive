from ceqr.helper.engines import recipe_engine, edm_engine, ceqr_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
import pandas as pd
from pathlib import Path
import numpy as np
import os

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
    
    SQL = f'''
        ALTER TABLE dec_facility_permits.latest ADD COLUMN id SERIAL PRIMARY KEY;

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
        '''

    os.system('echo "exporting table ..."')
    # export table to EDM_DATA
    exporter(df=df, 
             output_table=output_table,  
             DDL=DDL,
             sql=SQL)
             