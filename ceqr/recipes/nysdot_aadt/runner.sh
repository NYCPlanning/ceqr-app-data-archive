cd $(dirname $0)

# install dependencies
pip3 install -r requirements.txt

# build 
echo .
echo 'start building ...'
python3 build.py