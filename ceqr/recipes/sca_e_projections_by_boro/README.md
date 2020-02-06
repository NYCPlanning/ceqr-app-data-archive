# sca-enrollment-projections-by-boro

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish table `python3 build.py`

## Data info: 
* input:
  * `sca_e_projections.2019` in RECIPE_ENGINE
* output: 
  * `sca_e_projections_by_boro.latest` in EDM_DATA
* DDL: 
  ```sql
    CREATE TABLE sca_e_projections_by_boro."2019" (
      school_year integer,
      borocode integer,
      hs integer
    );
  ```