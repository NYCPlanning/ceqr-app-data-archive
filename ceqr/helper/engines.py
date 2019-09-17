from dotenv import load_dotenv, find_dotenv
from pathlib import Path
from sqlalchemy import create_engine
import os
load_dotenv(Path(__file__).parent.parent/'.env')

recipe_engine = create_engine(os.getenv('RECIPE_ENGINE'))
edm_engine = create_engine(os.getenv('EDM_DATA'))