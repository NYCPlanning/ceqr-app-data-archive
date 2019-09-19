# ctpp-journey-to-work

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish journey-to-work table and its lookup table `python3 build.py` 
3. build and publish total workers and mode-split table `python3 mode_split.py`

## Data info: 
* input:
  * `ctpp_journey_to_work."2019/09/16"` in RECIPE_ENGINE
* output: 
  * `ctpp_journey_to_work.2006_2010` in EDM_DATA
* DDL: 
  ```sql
  CREATE TABLE ctpp_journey_to_work."2006_2010" (
    residential_geoid character varying,
    work_geoid character varying,
    "MODE" character varying,
    count integer,
    standard_error double precision
  );
  ```
