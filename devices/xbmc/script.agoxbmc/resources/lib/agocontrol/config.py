import sys
import logging
import ConfigParser
from threading import Lock



logger = logging.Logger(__name__)
logger.addHandler(logging.NullHandler())

BINDIR = '/opt/agocontrol/bin'
CONFDIR = '/etc/opt/agocontrol'

CONFIG_LOCK = Lock()


def getConfigOption(section, option, default, filename=None):
    """Read a config option from a .ini style file."""
    config = ConfigParser.ConfigParser()
    CONFIG_LOCK.acquire(True)
    try:
        if file:
            config.read(CONFDIR + '/conf.d/' + filename + '.conf')
        else:
            config.read(CONFDIR + '/conf.d/' + section + '.conf')
        value = config.get(section,option)
    except ConfigParser.Error, e:
        logger.warning("Can't parse config file: %s", e)
        value = default
    finally:
        CONFIG_LOCK.release()
    return value


def setConfigOption(section, option, value, filename=None):
    """Write out a config option to a .ini style file."""
    config = ConfigParser.ConfigParser()
    result = False
    CONFIG_LOCK.acquire(True)
    try:
        path = CONFDIR + '/conf.d/' + section + '.conf'
        if file:
            path = CONFDIR + '/conf.d/' + filename + '.conf'
        #first of all read file
        config.read(path)
        #then update config
        if not config.has_section(section):
            config.add_section(section)
        config.set(section, option, str(value))
        #then write new file
        fpw = open(path, 'w')
        config.write(fpw)
        #finally close it
        fpw.close()
        result = True
    except ConfigParser.Error, e:
        logger.error("Can't write config file: %s", e)
        result = False
    finally:
        CONFIG_LOCK.release()
    return result