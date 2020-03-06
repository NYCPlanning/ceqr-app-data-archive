# atypical_roadways
A roadway that is either elevated or depressed compared to the surrounding environment. Not on the same level. If site is 200 feet from an Atypical Roadway then this needs to be considered in the CEQR air analysis.

We took all the roadways above or below the ground level from DCP LION data and excluded the bike paths as well as pedestrian overpasses.


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
