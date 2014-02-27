from time import time



class AgoRemoteDevice(object): 
    def __init__(self, connection, uuid):
        self.connection = connection
        self.uuid = uuid
        
    def __getattr__(self, command):
        return lambda **kwargs: self.connection.command(command, uuid=self.uuid, **kwargs)


class AgoEventHandler(object):
    bind_callbacks = {}
    
    def bind(self, event_type, callback):
        if not self.bind_callbacks:
            self.bind_callbacks = {}
        self.bind_callbacks.setdefault(event_type, [])
        self.bind_callbacks[event_type].append(callback)
        
    def event_callback(self, event_type, **content):
        callback_name = 'on_%s' % event_type[len('event.'):].replace('.', '_')
        if callback_name in dir(self):
            getattr(self, callback_name)(**content)
        
        if event_type in self.bind_callbacks:
            for callback in self.bind_callbacks[event_type]:
                callback(event_type, **content)

            
class AgoInventoryDevice(AgoRemoteDevice, AgoEventHandler):
    def __init__(self, connection, uuid, props):
        super(AgoInventoryDevice, self).__init__(connection, uuid)
        self.device_type = props.get('devicetype')
        self.handled_by = props.get('handled-by')
        self.internal_id = props.get('internalid')
        
        self.last_seen = props.get('lastseen')
        self.name = props.get('name')
        self.stale = bool(props.get('stale'))
        self.state = props.get('state')
        self.values = props.get('values')
        self.room = props.get('room')
        
    def on_device_announce(self, **content):
        self.device_type = content.get('devicetype')
        self.handled_by = content.get('handled-by')
        self.internal_id = content.get('internalid')
        self.stale = False
        self.last_seen = int(time())
        
    def on_system_devicenamechanged(self, name, **content):
        self.name = name
        
    def on_device_statechanged(self, level, **content):
        self.state = int(level)
        
        
class AgoRoom(AgoEventHandler):
    def __init__(self, name, location):
        self.name = name
        self.location = location
        self.devices = set()
        
    def add_device(self, device):
        self.devices.add(device)

    def remove_device(self, device):
        self.devices.remove(device)

    def event_callback(self, event_type, **content):
        for device in self.devices:
            device.event_callback(event_type, **content)
        super(AgoRoom, self).event_callback(event_type, **content)
        
    def on_system_roomnamechanged(self, name, **content):
        self.name = name
             
             
class AgoInventory(AgoEventHandler):
    def __init__(self, connection):
        self.connection = connection
        self.uuids = {}
        self.rooms = []
        self.devices = []
        
        inventory = connection.command('inventory')
        self.schema = inventory.get('schema', {})
        
        for uuid, props in inventory.get('rooms', {}).items():
            self.add_room(uuid, props)

        for uuid, props in inventory.get('devices', {}).items():
            if props.get('room'):
                props['room'] = self.uuids.get(props['room'])
            self.add_device(uuid, props)
            
        connection.set_event_callback(self.event_callback)
        
    def add_device(self, uuid, props):
        device = self.create_device(uuid, props)
        if device is not None:
            self.uuids[uuid] = device
            self.devices.append(device)
            if device.room:
                device.room.devices.add(device)
            self.event_callback('event.internal.newdevice', uuid=uuid, **props)

    def add_room(self, uuid, props):
        room = self.create_room(uuid, props)
        if room is not None:
            self.uuids[uuid] = room
            self.rooms.append(room)
    
    def create_device(self, uuid, props):
        return AgoInventoryDevice(self.connection, uuid, props)

    def create_room(self, uuid, props):
        return AgoRoom(props.get('name'), props.get('location'))
    
    def event_callback(self, event_type, **content):
        if event_type == 'event.system.deviceroomchanged':
            content['room'] = self.uuids.get(content.get('room'))
        if content.get('uuid') in self.uuids:
            self.uuids[content['uuid']].event_callback(event_type, **content)
        super(AgoInventory, self).event_callback(event_type, **content)
                
    def on_device_announce(self, uuid, **content):
        if uuid not in self.uuids:
            self.add_device(uuid, content)
        
    def on_system_deviceroomchanged(self, uuid, room):
        room = self.uuids.get(room)
        device = self.uuids.get(uuid)
        if device:
            device.room.devices.remove(device)
            device.room = room
        
    def on_system_roomnamechanged(self, uuid, **content):
        if uuid not in self.uuids:
            self.add_room(uuid, content)
    
    def on_device_remove(self, uuid, **content):
        device = self.uuids.pop(uuid)
        device.room.devices.remove(device)
        self.devices.remove(device)
        
    def on_system_roomdeleted(self, uuid, **content):
        room = self.uuids.pop(room)
        for device in room.devices:
            device.room = None
        self.rooms.remove(room)
