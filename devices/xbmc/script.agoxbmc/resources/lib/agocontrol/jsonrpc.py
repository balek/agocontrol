import httplib
import json
import logging



logger = logging.Logger(__name__)
logger.addHandler(logging.NullHandler())


class JSONRPCConnection(object):
    def __init__(self, host, path='/jsonrpc', https=False):
        if self.https:
            connection_class = httplib.HTTPSConnection
        else:
            connection_class = httplib.HTTPConnection
            
        self.connection = connection_class(host)
        self.path = path
        self.request_id = 0
    
    def request(self, method, **params):
        self.request_id += 1
        body = { 'jsonrpc': '2.0',
                 'id': self.request_id,
                 'method': method
               }
        if params:
            body['params'] = params
        self.connection.request('POST', self.path, json.dumps(body))
        response = self.connection.getresponse()
        return json.loads(response.read())['result']
    
    def __getattr__(self, name):
        return lambda **params: self.request(name, **params)
    

class AgoJSONRPCConnection:
    """This is class will handle the connection to ago control through JSON RPC interface."""
    
    def __init__(self, host=None, path='/jsonrpc', https=False):
        self.host = host
        self.path = path
        self.https = https
        self.event_callbacks = []
        self.command_callback = None

    def __del__(self):
        self.sender.close()
        self.receiver.close()

    def add_event_callback(self, callback, uuid=None, event_type=None, handler=None):
        self.event_callbacks.append((callback, uuid, event_type, handler))
        
    def open(self):
        logger.info('connecting to host %s', self.host)
            
        self.sender = JSONRPCConnection(self.host, self.path, self.https)
        self.receiver = JSONRPCConnection(self.host, self.path, self.https)
        self.subscription = self.receiver.subscribe()

    def _send_message(self, content, subject=None):
        """Send message and fetch reply if needed."""

        if subject is None:
            return self.sender.message(content=content)
        return self.sender.message(subject=subject, content=content)
            
    def emit_event(self, event_type, **content):
        return self._send_message(content=content, subject=event_type)
        
    def command(self, command, wait_reply=True, **content):
        content['command'] = command
        return self._send_message(content=content)

    def run(self):
        """This will start command and event handling. Be aware that this is blocking."""
        logger.info('startup complete, waiting for messages')
        while (True):
            try:
                result = self.receiver.getevent(uuid=self.subscription)
                if 'event' in result:
                    for callback, uuid, event_type, handler in self.event_callbacks:
                        if uuid and result.get('uuid') != uuid:
                            continue
                        if event_type and not result['event'].startswith(event_type):
                            continue
                        if handler and result.get('instance') != handler:
                            continue
                        callback(result.pop('event'), **result)
            except httplib.RequestTimeout, e:
                pass