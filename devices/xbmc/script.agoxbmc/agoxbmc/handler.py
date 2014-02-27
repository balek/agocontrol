import os
from socket import gethostname

import xbmc, xbmcaddon

from agocontrol.connection import AgoConnection, uuid4
from agocontrol.handler import AgoHandler, AgoDevice, agocommand



class XBMCHandler(AgoHandler):
    def __init__(self, connection):
        super(XBMCHandler, self).__init__(connection, 'xbmc')
        
    def load_uuid_map(self):
        pass
    
    def get_uuid(self, internal_id):
        addon_data_special_path = xbmcaddon.Addon().getAddonInfo('profile')
        addon_data_path = xbmc.translatePath(addon_data_special_path)
        path = os.path.join(addon_data_path, 'uuid.txt')
        try:
            return open(path).read().strip()
        except IOError:
            uuid = str(uuid4())
            dir_path = os.path.dirname(path)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
            open(path, 'w').write(uuid)
            return uuid
    

class XBMCDevice(AgoDevice, xbmc.Player):
    def __new__(cls, handler):
        return super(XBMCDevice, cls).__new__(cls)
        
    def __init__(self, handler):
        AgoDevice.__init__(self, handler, gethostname(), 'mediaplayer')
        xbmc.Player.__init__(self)
        
    def is_paused(self):
        return bool(xbmc.getCondVisibility("Player.Paused"))
    
    @agocommand
    def play(self, url):
        super(Device, self).play(url)
    
    @agocommand
    def play_pause(self):
        self.pause()
            
    @agocommand
    def seek(self, time):
        self.seekTime(time)
        
    @agocommand
    def stop(self):
        super(XBMCDevice, self).stop()
        
    @agocommand
    def next(self):
        self.playnext()
        
    @agocommand
    def previous(self):
        self.playprevious()
            
    def onPlayBackStarted(self):
        self.emit_event('event.device.mediastatechanged', state='playing')
#         self.emit_event('event.device.urlchanged', url=self.getPlayingFile())
        
    def onPlayBackStopped(self):
        self.emit_event('event.device.mediastatechanged', state='stopped')
#         self.emit_event('event.device.urlchanged', url='')
        
    def onPlayBackEnded(self):
        self.emit_event('event.device.mediastatechanged', state='stopped')
#         self.emit_event('event.device.urlchanged', url='')
        
    def onPlayBackPaused(self):
        self.emit_event('event.device.mediastatechanged', state='paused')
        
    def onPlayBackResumed(self):
        self.emit_event('event.device.mediastatechanged', state='playing')
        
#     def onQueueNextItem(self):
#         self.emit_event('event.device.urlchanged', url=self.getPlayingFile())