# doe-significant-utilization-changes

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish table `python3 build.py`

## Data info: 
* input:
  * `doe_all_proposals."2019/07/16"` in RECIPE_ENGINE
* output: 
  * `doe_significant_utilization_changes."072019"` in EDM_DATA
* DDL: 
  ```sql
  CREATE TABLE doe_significant_utilization_changes."072019" (
    bldg_id character varying,
    org_id character varying,
    bldg_id_additional character varying,
    title character varying,
    at_scale_year character varying,
    url character varying,
    at_scale_enroll integer,
    vote_date character varying);
  ```