cd $(dirname $0)

# install dependencies
pip3 install -r requirements.txt

# load the data into BUILD_ENGINE
python3 dataloading.py

# read the credentials
cd $(dirname "$(pwd)")
cd $(dirname "$(pwd)")
if [ -f .env ]
then
  export $(cat .env | sed 's/#.*//g' | xargs)
fi

# perform ETL
psql $BUILD_ENGINE -f recipes/ceqr_school_buildings/build.sql

# export the table to EDM_DATA
python3 recipes/ceqr_school_buildings/export.py