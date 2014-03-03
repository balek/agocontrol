import os, sys
import socket
from threading import Thread
import logging

import xbmc, xbmcaddon

_addon = xbmcaddon.Addon()
_addon_path = _addon.getAddonInfo('path')
sys.path.append(os.path.join(_addon_path, 'resources', 'lib'))

from symmetricjsonrpc import RPCClient
from agocontrol.connection import AgoConnection

from agoxbmc.dialog import AgoDialog
from agoxbmc.inventory import Inventory
from agoxbmc.handler import XBMCHandler, XBMCDevice



class XBMCLogHandler(logging.Handler):
    level_map = {
        logging.CRITICAL: xbmc.LOGFATAL,
        logging.ERROR: xbmc.LOGERROR,
        logging.WARNING: xbmc.LOGWARNING,
        logging.INFO: xbmc.LOGNOTICE,  # Enable INFO output even if XBMC's debug logging disabled
        logging.DEBUG: xbmc.LOGDEBUG,
        logging.NOTSET: xbmc.LOGNONE
    }

    def emit(self, record):
        xbmc.log(record.message, self.level_map[record.levelno])
        

class XBMCJSONRPCClient(RPCClient):
    class Request(RPCClient.Request):
        def dispatch_notification(self, subject):
            if subject['method'] == 'System.OnQuit':
                xbmc_jsonrpc_service.shutdown()
                return
            if subject['method'] != 'Other.AgoXBMC':
                return
            data = subject['params']['data']
            action = data.pop('action')
            if hasattr(self, 'action_' + action):
                getattr(self, 'action_' + action)(**data)
                
        def action_toggleDialog(self):
            if agodialog.active:
                agodialog.close()
            else:
                Thread(target=agodialog.doModal).start()
                
        def action_toggle(self, uuid):
            device = inventory.uuids.get(uuid)
            if hasattr(device, 'toggle'):
                device.toggle()
            
        def action_command(self, command, content):
            connection.command(command, **content)
            
            
            
logger = logging.Logger('root')
logger.addHandler(XBMCLogHandler())

xbmc_jsonrpc_service = None
agoconnection = None
agoconnection_thread = None
agodialog = None

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 9090))
    xbmc_jsonrpc_service = XBMCJSONRPCClient(s)
    xbmc_jsonrpc_service.request('JSONRPC.SetConfiguration', { 'notifications': { 'GUI': False,
                                                                    'Other': True,
                                                                    'Input': False,
                                                                    'VideoLibrary': False,
                                                                    'AudioLibrary': False,
                                                                    'Playlist': False,
                                                                    'System': True,
                                                                    'Player': False,
                                                                    'Application': False,
                                                                    'PVR': False,
                                                                  }
                                               })
    broker = _addon.getSetting('broker')
    username = _addon.getSetting('username')
    password = _addon.getSetting('password')
    agoconnection = AgoConnection(broker, username, password)
    agoconnection.open()
    handler = XBMCHandler(agoconnection)
    device = XBMCDevice(handler)
    inventory = Inventory(agoconnection)
    agodialog = AgoDialog(inventory)

    agoconnection_thread = Thread(target=agoconnection.run)
    agoconnection_thread.start()

    while not xbmc.abortRequested:
        xbmc.sleep(1000)
finally:
    if xbmc_jsonrpc_service:
        xbmc_jsonrpc_service.shutdown()
        xbmc_jsonrpc_service.join()
    
    if agodialog and agodialog.active:
        agodialog.close()
    
    if agoconnection:
        if agoconnection_thread:
            agoconnection.stop()
            agoconnection_thread.join()
        del agoconnection
        import atexit
        from qpid.selector import Selector
        atexit._exithandlers.remove((Selector.default().stop, (), {}))
        Selector.default().stop()