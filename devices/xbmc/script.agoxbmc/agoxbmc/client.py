import json

import xbmc



def agoxbmc_request(**kwargs):
    request = { 'jsonrpc': '2.0',
                'method': 'JSONRPC.NotifyAll',
                'id': 1,
                'params': { 'sender': 'agocontrol',
                            'message': 'AgoXBMC',
                            'data': kwargs
                          }
              }
    xbmc.executeJSONRPC(json.dumps(request))