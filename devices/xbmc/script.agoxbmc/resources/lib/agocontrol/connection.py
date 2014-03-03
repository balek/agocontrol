import logging
from time import sleep

from qpid.messaging import Connection, Message, uuid4, ReceiverError, SendError, MessagingError, Empty  # @UnresolvedImport

from .config import getConfigOption



logger = logging.Logger(__name__)
logger.addHandler(logging.NullHandler())

class CommandNotHandled(Exception): pass

class AgoConnection(object):
    """This is class will handle the connection to ago control."""
    
    connection = None
    stopped = False
    
    def __init__(self, broker=None, username=None, password=None):
        self.broker = broker or getConfigOption('system', 'broker', 'localhost')
        self.username = username or getConfigOption('system', 'username', 'agocontrol')
        self.password = password or getConfigOption('system', 'password', 'letmein')
        self.event_callback = None
        self.command_callback = None

    def __del__(self):
        if self.connection:
            self.connection.close()

    def set_event_callback(self, callback):
        self.event_callback = callback
        
    def set_command_callback(self, callback):
        self.command_callback = callback
        
    def open(self):
        logger.info('connecting to broker %s with username %s', self.broker, self.username)
        self.connection = Connection(self.broker, username=self.username, password=self.password, reconnect=True)
        self.connection.open()
        self.session = self.connection.session()
        self.receiver = self.session.receiver('agocontrol; {create: always, node: {type: topic}}')
        self.sender = self.session.sender('agocontrol; {create: always, node: {type: topic}}')

    def _send_message(self, content, subject=None, wait_reply=False):
        """Send message and fetch reply if needed."""
        
        replyreceiver = None
        try:
            message = Message(content=content, subject=subject)
            if wait_reply:
                replyuuid = str(uuid4())
                replyreceiver = self.session.receiver('reply-%s; {create: always, delete: always}' % replyuuid)
                message.reply_to = 'reply-%s' % replyuuid
                self.sender.send(message)
                replymessage = replyreceiver.fetch(timeout=3)
                self.session.acknowledge()
                return replymessage.content
            else:
                self.sender.send(message)
                return True
        except (Empty, ReceiverError) as e:
            return None
        except SendError, e:
            logger.error("Can't send message: %s", e)
            return False
        finally:
            if replyreceiver:
                replyreceiver.close()

    def _send_reply(self, addr, content):
        try:
            replysession = self.connection.session()  # Why do we need to create new session here?
            replysender = replysession.sender(addr)
            response = Message(content)
            replysender.send(response)
        except (SendError, AttributeError, MessagingError) as e:
            logger.error("can't send reply: %s", e)
        finally:
            replysession.close()
            
    def emit_event(self, event_type, **content):
        return self._send_message(content=content, subject=event_type)
        
    def command(self, command, wait_reply=True, **content):
        content['command'] = command
        return self._send_message(content=content, wait_reply=wait_reply)

    def stop(self):
        if self.connection:
            self.stopped = True
            self._send_message({})
        
    def run(self):
        """This will start command and event handling. Be aware that this is blocking."""
        logger.info('startup complete, waiting for messages')
        while not self.stopped:
            try:
                message = self.receiver.fetch()
                self.session.acknowledge()
                subject = message.subject or ''
                content = message.content or {}
                if subject.startswith('event.'):
                    self.event_callback(subject, **content)
                elif 'command' in content and self.command_callback:
                    command = content['command']
                    del content['command']
                    try:
                        returnval = self.command_callback(command, **content)
                    except CommandNotHandled:
                        continue
                    if message.reply_to:
                        if isinstance(returnval, dict):
                            self._send_reply(message.reply_to, returnval)
                        else:
                            self._send_reply(message.reply_to, { 'result': returnval })
            except Empty, e:
                pass

            except ReceiverError, e:
                logger.error("can't receive message: %s", e)
                sleep(0.05)