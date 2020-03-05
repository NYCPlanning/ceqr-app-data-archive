# atypical_roadways

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish table `python3 build.py`

## Data info: 
* input:
  * `dcp_lion.latest` in RECIPE_ENGINE
* output: 
  * `atypical_roadways.latest` in EDM_DATA
* DDL: 
  ```sql
  CREATE TABLE ceqr_school_buildings.latest (
    streetname text,
    segmentid text,
    streetwidth_min text,
    streetwidth_max text,
    right_zipcode text,
    left_zipcode text,
    borocode integer,
    nodelevelf text,
    nodelevelt text,
    featuretyp text,
    trafdir text,
    number_total_lanes text,
    bikelane text,
    geom geometry(LineString,4326)
  );
  ```
