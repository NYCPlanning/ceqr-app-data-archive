from geosupport import Geosupport, GeosupportError
import usaddress
import re
from shapely.geometry import Point

g = Geosupport()

def get_hnum(address):
    address = '' if address is None else address
    result = [k for (k,v) in usaddress.parse(address) \
            if re.search("Address", v)]
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

def geo_parser(geo):
    return dict(
        geo_housenum = geo.get('House Number - Display Format', ''),
        geo_streetname = geo.get('First Street Name Normalized', ''),
        geo_bbl = geo.get('BOROUGH BLOCK LOT (BBL)', {}).get('BOROUGH BLOCK LOT (BBL)', '',),
        geo_bin = geo.get('Building Identification Number (BIN) of Input Address or NAP', ''),
        geo_latitude = geo.get('Latitude', ''),
        geo_longitude = geo.get('Longitude', ''),
        geo_grc = geo.get('Geosupport Return Code (GRC)', ''),
        geo_grc2 = geo.get('Geosupport Return Code 2 (GRC 2)', ''),
        geo_reason_code = geo.get('Reason Code', ''),
        geo_message = geo.get('Message', 'msg err')
    )