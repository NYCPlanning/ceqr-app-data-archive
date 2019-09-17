cd $(dirname $0)

# install dependencies
pip3 install -r requirements.txt

# run web scraping script
echo .
echo 'running webscraping ...'
python3 scraper.py

# run web build script
echo .
echo 'start building ...'
python3 build.py