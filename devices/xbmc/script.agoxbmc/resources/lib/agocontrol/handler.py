import logging

import simplejson
from qpid.messaging import uuid4  # @UnresolvedImport

from .connection import CommandNotHandled
from .config import CONFDIR



logger = logging.Logger(__name__)
logger.addHandler(logging.NullHandler())


class agocommand_renamed:
    def __init__(self, name=None):
        self.name = name
    
    def __call__(self, func):
        if self.name:
            func.agocommand = self.name
        else:
            func.agocommand = func.__name__
        return func


def agocommand(func):
    return agocommand_renamed()(func)
    
    
class AgoDevice(object):
    class __metaclass__(type):
        def __new__(cls, name, bases, dict_):
            commands = {}
            for f in dict_.values():
                if hasattr(f, 'agocommand'):
                    commands[f.agocommand] = f
            dict_['commands'] = commands
            return type.__new__(cls, name, bases, dict_)
        
    def __init__(self, handler, internal_id, device_type):
        self.handler = handler
        self.internal_id = internal_id
        self.device_type = device_type
        self.uuid = handler.add_device(self)
        
    def emit_event(self, event_type, **content):
        content['uuid'] = self.uuid
        self.handler.emit_event(event_type, **content)

    def command_callback(self, command, **content):
        if command not in self.commands:
            raise CommandNotHandled
        return self.commands[command](self, **content)
        
        
class AgoHandler(object):
    """This is class to handle devices"""
    
    def __init__(self, connection, name):
        self.connection = connection
        self.name = name
        self.devices = {}
        self.uuids = {}
        self.load_uuid_map()
        connection.set_command_callback(self.command_callback)
    
    def emit_event(self, event_type, **content):
        content['instance'] = self.name
        return self.connection.emit_event(event_type, **content)

    def emit_device_announce(self, uuid, device):
        """Send a device announce event, this will be honored by the resolver component.

        You can find more information regarding the resolver here: http://wiki.agocontrol.com/index.php/Resolver """
        content = {
            'uuid': uuid,
            'devicetype': device.device_type,
            'internalid': device.internal_id,
            'handled-by': self.name
        }
        self.emit_event('event.device.announce', **content)

    def emit_device_remove(self, uuid):
        self.emit_event('event.device.remove', uuid=uuid)

    def uuid_map_path(self):
        return CONFDIR + '/uuidmap/' + self.name + '.json'
    
    def store_uuid_map(self):
        """Store the mapping (dict) of UUIDs to internal ids into a JSON file."""
        try:
            with open(self.uuid_map_path() , 'w') as outfile:
                simplejson.dump(self.uuids, outfile)
        except (OSError, IOError) as e:
            logger.error('Cannot write uuid map file: %s', e)
        except ValueError, e:  # includes simplejson error
            logger.error('Cannot encode uuid map: %s', e)

    def load_uuid_map(self):
        """Read the mapping (dict) of UUIDs to internal ids from a JSON file."""
        try:
            with open(self.uuid_map_path(), 'r') as infile:
                self.uuids = simplejson.load(infile)
        except (OSError, IOError) as e:
            logger.error('Cannot load uuid map file: %s', e)
        except ValueError, e:  # includes simplejson.decoder.JSONDecodeError
            logger.error('Cannot decode uuid map: %s', e)

    def report_devices(self):
        """Report all our devices."""
        logger.info('reporting child devices')
        for uuid, device in self.devices.items():
            self.emit_device_announce(uuid, device)

    def get_uuid(self, internal_id):
        if internal_id not in self.uuid_map:
            self.uuid_map[internal_id] = str(uuid4())
            self.store_uuid_map()
        return self.uuid_map[internal_id]
        
    def add_device(self, device):
        """Add a device. Announcement to ago control will happen automatically. Commands to this device will be dispatched to the command handler.
        The devicetype corresponds to an entry in the schema."""
        uuid = self.get_uuid(device.internal_id)
        self.devices[uuid] = device
        self.emit_device_announce(uuid, device)
        return uuid

    def remove_device(self, uuid):
        if (uuid in self.devices): 
            self.emit_device_remove(uuid)
            del self.devices[uuid]
            
    def command_callback(self, command, **content):
        if command == 'discover':
            self.report_devices()
            return
        try:
            uuid = content.pop('uuid')
            device = self.devices[uuid]
        except KeyError:
            raise CommandNotHandled
        return device.command_callback(command, **content)
