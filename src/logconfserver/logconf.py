import collections
import socket
import struct
import re
import threading
import ConfigParser

import filewatch

class LogConf(object):
    """ Simple logconfiguration control/querying
    """

    def __init__(logconf_file, ports):
        self.ports = ports
        self.free_ports = collections.deque(ports)
        self.used_ports = collections.deque
        self.logconf_file = logconf_file
        self.parser = ConfigParser.SafeConfigParser()
        self.stop = threading.Event()
        self.stop.clear()
        filewatch.FileWatcher(logconf_file, self.notify_listeners).start()

    def __del__(self):
        self.stop.set()

    
    def notify_listeners(self, filename, listeners = None):
        if not listeners:
            listeners = self.used_ports
        with open(filename) as f:
            contents = f.read()
            contents_len = len(contents)
            for port in listeners:
                self.send_to_port(contents, port, len=len)

    def send_to_port(self, contents, port, len = None):
        if not len:
            len = len(contents)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect('localhost', port)
        s.send(struct.pack('>L', len))
        s.send(contents)
        s.close()            

    def register(self):
        if self.free_ports:
            port = self.free_ports.pop()
            self.used_ports.append(port)
            return port
        else:
            return None
    
    def unregister(self, port):
        if port in self.used_ports:
            self.free_ports.append(port)
            self.used_ports.remove(port)

    
    self.set_level(self, logger_levels):
        """
        logger_levels is a sequence of (logger, level) pairs,
        where logger is a string naming a logger and level is a number
        """
        self.parser.read(self.filename)
        changed = False
        for logger, level in logger_levels:
            sec_name = 'logger_%s' % logger
            current_level = int(sec_name, 'level'))
            if level != current_level:
                self.parser.set(secname, 'level', level)
                changed = True
        if changed:
            with open(self.filename, 'w') as f:
                self.parser.write(f)

            
        
