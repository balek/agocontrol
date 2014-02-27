from agocontrol.connection import AgoConnection
from agocontrol.inventory import AgoInventory, AgoInventoryDevice

connection = AgoConnection('cr', 'agocontrol', 'letmein')
connection.open()
inventory = AgoInventory(connection)
print inventory.rooms, inventory.devices