import os, sys



if not sys.argv[1:]:
    path = os.path.dirname(__file__)
    execfile(os.path.join(path, 'agoxbmc/service.py'))

else:
    from agoxbmc.client import agoxbmc_request
    
    content = {}
    for arg in sys.argv[1:]:
        param, val = arg.split('=', 1)
        content[param] = val
    agoxbmc_request(**content)