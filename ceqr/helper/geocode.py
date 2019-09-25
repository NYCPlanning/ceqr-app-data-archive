from geosupport import Geosupport, GeosupportError
import usaddress
import re
g = Geosupport()

def get_hnum(address):
    result = [k for (k,v) in usaddress.parse(address) \
            if re.search("Address", v)]  if address is not None else ''
    result = ' '.join(result)
    return result

def get_sname(address):
    result = [k for (k,v) in usaddress.parse(address) \
            if re.search("Street", v)]  if address is not None else ''
    result = ' '.join(result)
    if result == '':
        return address
    else: 
        return result