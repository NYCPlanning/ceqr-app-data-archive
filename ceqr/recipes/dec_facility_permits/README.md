# dec-facility-permits

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish table `python3 build.py`

## Data info: 
* input:
  * `dec_state_facility_permits.latest` in RECIPE_ENGINE
  * `dec_title_v_facility_permits.latest` in RECIPE_ENGINE
* output: 
  * `dec_facility_permits.latest` in EDM_DATA
* DDL: 
  ```sql
  CREATE TABLE dec_facility_permits.latest (
    facility_name text,
    permit_id text,
    url_to_permit_text text,
    facility_location text,
    facility_city text,
    facility_state text,
    facility_zip text,
    issue_date text,
    expire_date text,
    location text,
    source text,
    geom geometry(Point,4326)
  );
  ```