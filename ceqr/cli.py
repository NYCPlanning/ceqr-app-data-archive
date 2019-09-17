import os
from pathlib import Path
import click
import json
from cook import Archiver
import pandas as pd
import numpy as np
from ast import literal_eval

@click.group()
def cli():
    pass

@cli.command('run')
@click.argument('recipe', type=click.STRING)
def run_recipes(recipe):
    click.secho(f'\nrunning {recipe} ...\n', fg='red')
    os.system(f'bash {Path(__file__).parent}/recipes/{recipe}/runner.sh')