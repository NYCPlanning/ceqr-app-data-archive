# sca_capital_projects

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish table `python3 build.py`

## Data info: 
* input:
  * `sca_capital_projects."2019/09/11"` in RECIPE_ENGINE
* output: 
  * `sca_capital_projects.latest` in EDM_DATA
* DDL: 
  ```sql
  CREATE TABLE sca_capital_projects.latest (
      project_dsf text,
      name text,
      org_level text,
      capacity bigint,
      pct_ps double precision,
      pct_is double precision,
      pct_hs double precision,
      guessed_pct boolean,
      start_date text,
      planned_end_date text,
      total_est_cost double precision,
      funding_current_budget double precision,
      funding_previous double precision,
      pct_funded double precision,
      geometry geometry(Point,4326)
  );
  ```