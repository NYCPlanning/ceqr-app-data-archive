from bs4 import BeautifulSoup
import requests
from pathlib import Path
import dateutil.parser as dparser
import re 
import urllib
from itertools import groupby
import pandas as pd

def extract_date(x): 
    try: 
        dt = dparser.parse(x, fuzzy=True)
        return dt.date()
    except:
        pass

def get_date(url):
    url = url.split('&')[0].split('Public Notice')[0]
    paths = Path(url).parts
    lst =  list(filter(lambda x: x is not None, map(extract_date, paths)))
    return lst[0].isoformat()

def get_school_year(url):
    url = url.split('&')[0]
    p = Path(url).parts
    school_year = str(p[11])
    return school_year

if __name__ == "__main__":
    base_url = 'https://www.schools.nyc.gov'
    url = 'https://www.schools.nyc.gov/about-us/leadership/panel-for-education-policy'
    url1 = 'https://www.schools.nyc.gov/about-us/leadership/panel-for-education-policy/pep-meetings-archive'
    html_doc = requests.get(url).content
    soup = BeautifulSoup(html_doc, 'html.parser')

    html_doc1 = requests.get(url1).content
    soup1 = BeautifulSoup(html_doc1, 'html.parser')

    proposals = []

    # get all proposal urls
    for a in soup.find_all('a', href=True):
        url = a['href']
        if 'sharepoint' in url:
            try:
                r = requests.get(url)
                readable_url = urllib.parse.unquote(r.url)
                if 'Contracts' in readable_url:
                    pass
                else: 
                    date = get_date(readable_url)
                    school_year = get_school_year(readable_url)
                    proposals.append(dict(url = a['href'],
                                        school_year = school_year, 
                                        readable_url = readable_url,
                                        date = date))
            except: 
                pass
        else:
            continue

    for a in soup1.find_all('a', href=True):
        url = a['href']
        if 'sharepoint' in url:
            try:
                r = requests.get(url)
                readable_url = urllib.parse.unquote(r.url)
                if 'Contracts' in readable_url:
                    pass
                else:
                    try:
                        date = get_date(readable_url)
                        school_year = get_school_year(readable_url)
                        proposals.append(dict(url = a['href'],
                                            school_year = school_year,
                                            readable_url = readable_url,
                                            date = date))
                    except:
                        school_year = get_school_year(readable_url)
                        proposals.append(dict(url = a['href'],
                                            readable_url = readable_url,
                                            school_year = school_year,
                                            date = ''))
            except: 
                pass
        else:
            continue

        proposals1 = []
        for k, g in groupby(proposals, lambda x: x['date']+x['school_year']):
            g1 = min(g, key=lambda x: len(x['readable_url']))
            proposals1.append(g1)
        
        df = pd.DataFrame(proposals1)
        df.to_csv(str(Path(__file__).parent/'output/sharepoint_urls.csv'))