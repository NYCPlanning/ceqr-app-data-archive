# ceqr-app-data
Includes data pipelines for CEQR app, managed by data engineering

## Instructions
1. Set environmental variables: `RECIPE_ENGINE`, `CEQR_DATA`, and `EDM_DATA`. See `.env.example`.
2. Run `python3 -m venv base` to set up the virtual environment.
3. Run `source base/bin/activate` to activate the virtual environment. To deactivate once finished, type `deactivate`.
4. Run `pip3 install -e .` to install packages required accross multiple data schema.
4. Run `ceqr run <data schema>` at root directory. For example, `ceqr run ceqr_school_buildings`. This will also install required
packages specific to the data schema. 