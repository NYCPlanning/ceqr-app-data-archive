# ctpp-censustract-variables

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish journey-to-work table and its lookup table `python3 build.py` 
3. build and publish total workers and mode-split table `python3 mode_split.py`

## Data info: 
* input:
  * `ctpp_mode_split_ny."2012_2016"` in RECIPE_ENGINE
* output: 
  * `ctpp_censustract_variables.2012_2016` in EDM_DATA
* DDL: 
  ```sql
  CREATE TABLE ctpp_censustract_variables."2012_2016" (
    geoid text,
    value bigint,
    moe bigint,
    variable text
  );
  ```
