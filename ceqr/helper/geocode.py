from geosupport import Geosupport, GeosupportError
import usaddress
import re
from shapely.geometry import Point

g = Geosupport()

def get_hnum(address):
    result = [k for (k,v) in usaddress.parse(address) \
            if re.search("Address", v)]  if address is not None else ''
    result = ' '.join(result)
    fraction = re.findall('\d+[\/]\d+', address)
    if not bool(re.search('\d+[\/]\d+', result)) and len(fraction) != 0:
           result = f'{result} {fraction[0]}' 
    return result

def get_sname(address):
    result = [k for (k,v) in usaddress.parse(address) \
            if re.search("Street", v)]  if address is not None else ''
    result = ' '.join(result)
    if result == '':
        return address
    else: 
        return result

def create_geom(lon, lat):
        lon = float(lon) if lon != '' else None
        lat = float(lat) if lat != '' else None
        if (lon is not None) and (lat is not None): 
                return str(Point(lon, lat))