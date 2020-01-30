cd $(dirname $0)

# install dependencies
pip3 install -r requirements.txt
apt install libspatialindex-dev python-rtree

# run script
python3 build.py