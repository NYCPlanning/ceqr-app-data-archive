# ceqr-school-buildings

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish table `python3 build.py`

## Data info: 
* input:
  * `doe_lcgms.latest` in RECIPE_ENGINE
  * `sca_bluebook.latest` in RECIPE_ENGINE
  * `dcp_boroboundaries_wi.latest` in RECIPE_ENGINE
  * `doe_school_subdistricts.latest` in RECIPE_ENGINE
* output: 
  * `ceqr_school_buildings.latest` in EDM_DATA
* DDL: 
  ```sql
  CREATE TABLE ceqr_school_buildings.latest (
    district integer,
    subdistrict integer,
    borocode integer,
    bldg_name character varying,
    excluded boolean,
    bldg_id character varying,
    org_id character varying,
    org_level character varying,
    "name" character varying,
    "address" character varying,
    pc integer,
    pe integer,
    ic integer,
    ie integer,
    hc integer,
    he integer,
    source text,
    geom geometry(Point,4326)
  );

  ```
