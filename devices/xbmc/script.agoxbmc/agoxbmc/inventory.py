import os

from xbmcgui import ListItem
import xbmcaddon

from pyxbmct.addonwindow import *
from agocontrol.inventory import AgoInventory, AgoInventoryDevice

        
        
_addon_path = xbmcaddon.Addon().getAddonInfo('path')

class Device(AgoInventoryDevice):
    def __init__(self, connection, uuid, props):
        super(Device, self).__init__(connection, uuid, props)
        self.list_item = ListItem(self.get_label(), self.get_label2(), self.get_icon(), '', '')
        self.list_item.setProperty('uuid', uuid)
        
    def get_label(self):
        if not self.room:
            return ''
        return '%s - %s' % (self.room.name, self.name)
    
    def get_label2(self):
        return str(self.state)
    
    def get_icon(self):
        path = os.path.join(_addon_path, 'resources', 'media', self.device_type + '.png')
        if os.path.exists(path):
            return path
        return ''
    
    def onMoveLeft(self): pass
    def onMoveRight(self): pass
    def onClick(self): pass
    
    def on_system_deviceroomchanged(self, **content):
        self.list_item.setLabel(self.get_label())
        
    def on_system_devicenamechanged(self, **content):
        super(Device, self).on_system_devicenamechanged(**content)
        self.list_item.setLabel(self.get_label())
        
    def on_system_roomnamechanged(self, **content):
        self.list_item_setLabel(self.get_label())
    
    def on_device_statechanged(self, level, **content):
        super(Device, self).on_device_statechanged(level, **content)
        self.list_item.setLabel2(self.get_label2())
        
        
class OnDevice(Device):
    def onClick(self):
        self.on()
            
            
class OnOffDevice(Device):
    def onClick(self):
        self.toggle()
        
    def toggle(self):
        if self.state:
            self.off()
        else:
            self.on()
            
              
class SetLevelDevice(OnOffDevice):
    def onMoveLeft(self):
        if self.state > 5:
            self.setlevel(level=(self.state - 5))

    def onMoveRight(self):
        if self.state < 95:
            self.setlevel(level=(self.state + 5))


class MediaPlayer(Device):
    def onClick(self):
        player = xbmc.Player()
        if not xbmc.getCondVisibility("Player.Paused"):
            player.pause()
        self.device.play(player.getPlayingFile())
        self.device.pause()
        self.device.seek(player.getTime())
        
        
class Inventory(AgoInventory):      
    def create_device(self, uuid, props):
        devicetype = props.get('devicetype')
        if not devicetype:
            return
        if devicetype == 'mediaplayer':
            return MediaPlayer(self.connection, uuid, props)
        
        commands = self.schema['devicetypes'].get(devicetype, {}).get('commands', [])
        if 'on' in commands:
            if 'off' in commands:
                if 'setlevel' in commands:
                    return SetLevelDevice(self.connection, uuid, props)
            return OnOffDevice(self.connection, uuid, props)
        return OnDevice(self.connection, uuid, props)