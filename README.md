## CEQR App Data User Guides
This repository includes ETL pipelines for all the datasets fed into CEQR (City Environmental Quality Review) app. It is managed by NYC Planning's data engineering team.

#### Building Instructions
1. Set environmental variables: `RECIPE_ENGINE`, `CEQR_DATA`, `BUILD_ENGINE`,and `EDM_DATA` under the `/ceqr` directory. See `.env.example`.
2. Run `python3 -m venv base` to set up the virtual environment.
3. Run `source base/bin/activate` to activate the virtual environment. To deactivate once finished, type `deactivate`.
4. Run `pip3 install -e .` to install packages required accross multiple data schema.
4. Run `ceqr run <schema_name>` at root directory. For example, `ceqr run ceqr_school_buildings`, which allows you to build `ceqr_school_buildings` from scratch

#### Repo directory structure
1. The ETL pipelines have been stored under the `/ceqr/recipes` directory as individual folders named by the datasets.
2. Each dataset subfolder contains the following items.
   - `build.py` A python script that will transform and integrate source datas into a target table
   - `config.json` A configuration file specifying the input table names, output table name and DDL (output table schemas).
     - It is noted that the DDLs of "nysdec_state_facility_permits", "nysdec_title_v_facility_permits" and "sca_capacity_projects" actually reflect the schemas for their `geo_rejects` tables
   - `README.md` The metadata about the ETL pipeline
   - `requirements` The required dependencies need to install to run the python script
   - `runner.sh` A shell script, by executing which, you can build a dataset from scratch. or you can execute `ceqr run <schema_name>` at root directory
```
├── ceqr
│   ├── recipes
│   │   ├── <schema_name_1>
│   │   │   ├── build.py
│   │   │   ├── config.json
│   │   │   ├── README.md
│   │   │   ├── requirements.txt
│   │   │   └── runner.sh
│   │   ├── <schema_name_2>
│   │   │   ├── build.py
│   │   │   ├── config.json
│   │   │   ├── README.md
│   │   │   ├── requirements.txt
│   │   │   └── runner.sh
...
```

#### How to build a new dataset
1. Create a new folder named by the dataset and put it under the `/ceqr/recipes` directory
2. Create `config.json`, `README.md`, `build.py`, `requirements.txt` and `runner.sh` as described in the **Repo directory structure** within this new folder
   - For the `output table schema`, besides the requirements specified by the data users, it also need to follow the [CEQR data schema standards](https://docs.google.com/spreadsheets/d/1Z41fgiU_mi1KltlS783kUZpPcC8Sn7hUxTqhaNxQFg8/edit?usp=sharing).
2. Follow the **Building Instructions** to test the ETL pipeline
3. Output table can be found in EDM_DATA under a schema named by the dataset.