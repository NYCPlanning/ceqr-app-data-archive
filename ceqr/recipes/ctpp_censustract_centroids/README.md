# ctpp-censustract-centroids

## Instructions: 
1. install dependencies `pip3 install -r requirements.txt`
2. build and publish journey-to-work table and its lookup table `python3 build.py` 
3. build and publish total workers and mode-split table `python3 mode_split.py`

## Data info: 
* input:
  * `ctpp_journey_to_work."2006_2010"` in EDM_DATA
* output: 
  * `ctpp_censustract_centroids.2006_2010` in EDM_DATA
* DDL: 
  ```sql
  CREATE TABLE ctpp_censustract_centroids."2006_2010" (
        geoid character varying,
        centroid geometry(Point,4326)
  );
  ```
