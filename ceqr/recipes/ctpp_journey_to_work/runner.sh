# install dependencies
pip3 install -r requirements.txt

# build journey-to-work table and its lookup table
python3 build.py

# build total workers and mode-split table
python3 mode_split.py