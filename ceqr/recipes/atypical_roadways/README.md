# atypical_roadways
A roadway that is either elevated or depressed compared to the surrounding environment. Not on the same level. If site is 200 feet from an Atypical Roadway then this needs to be considered in the CEQR air analysis.

We took all the roadways above or below the ground level from DCP LION data and excluded the bike paths as well as pedestrian overpasses.

<iframe style="height:600px" src="https://render.githubusercontent.com/view/geojson?commit=3684ba3313d535ce494f50fb0c9e31aa8ba4f3bc&amp;enc_url=68747470733a2f2f7261772e67697468756275736572636f6e74656e742e636f6d2f676973742f5350544b4c2f61666462373061313230393461616662626230623961633765666633383131662f7261772f333638346261333331336435333563653439346635306662306339653331616138626134663362632f617479706963616c5f726f6164776179732e67656f6a736f6e&amp;nwo=SPTKL%2Fafdb70a12094aafbbb0b9ac7eff3811f&amp;path=atypical_roadways.geojson&amp;repository_id=98765964&amp;repository_type=Gist#46885197-e76c-4d6f-bfc2-4e8c35077096" sandbox="allow-scripts allow-same-origin allow-top-navigation" title="File display">
          Viewer requires iframe.
      </iframe>

> Note: This dataset is manually created using [geojson.io](geojson.io), you can download the gist [here](https://gist.github.com/SPTKL/afdb70a12094aafbbb0b9ac7eff3811f)

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
