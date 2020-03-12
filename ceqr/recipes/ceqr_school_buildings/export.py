from ceqr.helper.engines import build_engine
from ceqr.helper.config_loader import load_config
from ceqr.helper.exporter import exporter
from pathlib import Path
import geopandas as gpd

if __name__ == "__main__":
    # Load configuration
    config = load_config(Path(__file__).parent/'config.json')
    output_table = config['outputs'][0]['output_table']
    DDL = config['outputs'][0]['DDL']
    
    df = gpd.GeoDataFrame.from_postgis(f'SELECT * FROM ceqr_school_buildings', con=build_engine, geom_col='geom')

    # Change school field type to integer
    for column in ['pc', 'ic', 'hc', 'pe', 'ie', 'he']:
        df[column] = df[column].fillna(0).astype(float).astype(int)


    # export table to EDM_DATA
    exporter(df=df,
             output_table=output_table,  
             DDL=DDL,
             sep='~',
             geo_column='geom')