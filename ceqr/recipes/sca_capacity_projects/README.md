# sca_capacity_projects

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish table `python3 build.py`

## Data info: 
* input:
  * `sca_capacity_projects_prev.latest` in RECIPE_ENGINE
  * `sca_capacity_projects_current.latest` in RECIPE_ENGINE
* output: 
  * `sca_capacity_projects.latest` in EDM_DATA
* DDL: 
  ```sql
  CREATE TABLE sca_capital_projects.latest (
      name text,
      org_level text,
      capacity bigint,
      pct_ps double precision,
      pct_is double precision,
      pct_hs double precision,
      guessed_pct boolean,
      opening_date date,
      capital_plan text,
      geometry geometry(Point,4326)
  );
  ```