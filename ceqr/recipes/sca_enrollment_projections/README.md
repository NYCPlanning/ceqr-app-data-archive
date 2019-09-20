# sca-enrollment-projections

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish table `python3 build.py`

## Data info: 
* input:
  * `sca_enrollment_pct_by_sd.latest` in RECIPE_ENGINE
  * `sca_enrollment_projections_by_sd.latest` in RECIPE_ENGINE
* output: 
  * `sca_enrollment_projections.latest` in EDM_DATA
* DDL: 
  ```sql
    CREATE TABLE sca_enrollment_projections."latest" (
        school_year integer,
        district integer,
        subdistrict integer,
        ps integer,
        is integer
    );
  ```