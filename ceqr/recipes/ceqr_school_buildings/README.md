# ceqr-school-buildings

## Instructions: 
1. Run `sh runner.sh` in the current directory to build the dataset

## Data info: 
* input:
  * `doe_lcgms.latest` in RECIPE_ENGINE
  * `sca_bluebook.latest` in RECIPE_ENGINE
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
    geom geometry(Point,4326)
  );

  ```
