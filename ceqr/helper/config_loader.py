import json

def load_config(path):
    ''' 
    load_config takes in a json file 
    and spits out a dictionary
    '''
    config = json.loads(open(path).read())
    return config