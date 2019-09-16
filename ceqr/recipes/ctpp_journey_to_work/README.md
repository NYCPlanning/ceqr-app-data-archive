# ctpp-journey-to-work

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish table `python3 build.py` and `python3 mode_split.py`

## Data info: 
* input:
  * `ctpp_journey_to_work."2019/09/16"` in RECIPE_ENGINE
  * `ctpp_mode_splits."NY_2006thru2010"` in RECIPE_ENGINE
  * `ctpp_mode_splits."NY_2012thru2016"` in RECIPE_ENGINE
* output: 
  * `ctpp_journey_to_work.2006_2010` in EDM_DATA
  * `ctpp_censustract_lookup.2006_2010` in EDM_DATA
  * `ctpp_censustract_variables.2006_2010` in EDM_DATA
  * `ctpp_censustract_variables.2012_2016` in EDM_DATA
* DDL: 
  ```sql
  CREATE TABLE ctpp_censustract_lookup."2006_2010" (
        geoid character varying,
        centroid geometry(Point,4326)
  );
  ```
