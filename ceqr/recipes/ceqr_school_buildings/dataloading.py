from ceqr.helper.engines import recipe_engine, build_engine
from ceqr.helper.config_loader import load_config
import pandas as pd
from pathlib import Path

if __name__ == "__main__":
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    input_table_bluebook = config['inputs'][0]
    input_table_lcgms = config['inputs'][1]

    bluebook = pd.read_sql(f'SELECT * FROM {input_table_bluebook}', con = recipe_engine)
    lcgms = pd.read_sql(f'SELECT * FROM {input_table_lcgms}', con = recipe_engine)

    bluebook.rename(columns={'ps_%': "ps_per", 'ms_%': "ms_per",'hs_%': "hs_per"}, inplace = True)

    bluebook.to_sql('sca_bluebook', con=build_engine, if_exists='replace', chunksize=1000, index=False)
    lcgms.to_sql('doe_lcgms', con=build_engine, if_exists='replace', chunksize=1000, index=False)