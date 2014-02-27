from xbmcgui import ListItem

from pyxbmct.addonwindow import *



class AgoDialog(AddonDialogWindow):
    active = False
    
    def __init__(self, inventory):
        super(AgoDialog, self).__init__('Test')
        self.inventory = inventory
        self.setGeometry(500, 500, 5, 5)
        self.device_list = List(_imageWidth=100, _imageHeight=100, _itemHeight=100)
        self.placeControl(self.device_list, 0, 0, columnspan=5, rowspan=5)
        self.fill_device_list()
        self.setFocus(self.device_list)
        self.connect(self.device_list, self.onDeviceListClick)
        self.connect(ACTION_MOVE_LEFT, self.onMoveLeft)
        self.connect(ACTION_MOVE_RIGHT, self.onMoveRight)
        self.connect(ACTION_NAV_BACK, self.close)
        
        for event_type in ( 'event.device.announce',
                            'event.device.remove',
                            'event.system.devicenamechanged',
                            'event.system.roomnamechanged',
                            'event.system.roomdeleted' ):
            inventory.bind(event_type, lambda et, **kw: self.fill_device_list())

    def fill_device_list(self):
        self.device_list.reset()
        rooms = [ r for r in self.inventory.rooms if r.name ]
        for room in sorted(rooms, lambda x, y: cmp(x.name, y.name)):
            for device in sorted(room.devices, lambda x, y: cmp(x.name, y.name)):
                self.device_list.addItem(device.list_item)
        
    def doModal(self):
        self.active = True
        super(AgoDialog, self).doModal()
        
    def close(self):
        self.active = False
        super(AgoDialog, self).close()
        
    def get_selected_device(self):
        uuid = self.device_list.getSelectedItem().getProperty('uuid')
        return self.inventory.uuids[uuid]
    
    def onDeviceListClick(self):      
        self.get_selected_device().onClick()
        
    def onMoveLeft(self):
        if self.getFocus() == self.device_list:
            self.get_selected_device().onMoveLeft()
        
    def onMoveRight(self):
        if self.getFocus() == self.device_list:
            self.get_selected_device().onMoveRight()