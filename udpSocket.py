import threading
import socket as s
import struct
from debug import *

BUF_SIZE = 1500

class UDPSocket(object):

    def __init__(self,
                 port,
                 ip='',
                 callback = lambda x: print(x)):
        
        self.ip = ip
        self.port = port
        self.sock = self.createSocket(ip,port)
        self.callback = callback

        dprint("UDPSocket: Iniciando a thread que ouve")
        thread = threading.Thread(target=_waitMessage,
                                  args=(self,self.callback))
        thread.daemon = True
        thread.start()
        
    def send(self, message, ip, port):
        self.sock.sendto(message,(ip,port))

    def createSocket(self,ip,port):
        dprint("Criando socket UPDSocket")
        sock = s.socket(s.AF_INET, s.SOCK_DGRAM, s.IPPROTO_UDP)
        sock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
        sock.bind((ip,port))
        return sock
        
class MulticastUDPSocket(UDPSocket):
        
    def __init__(self,
                 port,
                 multicastGroup,
                 ip='',
                 callback = lambda x: print(x)):
        
        self.ip = ip
        self.port = port
        self.multicastGroup = multicastGroup
        self.sock = self.createSocket(ip,port,multicastGroup)
        self.callback = callback

        dprint("MulticastUDP: Iniciando a thread que ouve")
        thread = threading.Thread(target=_waitMessage,
                                  args=(self,self.callback))
        thread.daemon = True
        thread.start()
        
    def send(self, message):
        dprint("MulticastUDP: sending message")
        self.sock.sendto(message, (self.ip,self.port))
        
    def createSocket(self, ip, port, multicastGroup):
        dprint("Criando socket MulticastUPDSocket")
        sock = super().createSocket(ip,port)
        sock.setsockopt(s.IPPROTO_IP, s.IP_MULTICAST_TTL, 1)
        mreq = struct.pack("=4sl",
                           s.inet_aton(self.multicastGroup),
                           s.INADDR_ANY)
        try:
            sock.setsockopt(s.IPPROTO_IP, s.IP_ADD_MEMBERSHIP, mreq)
        except OSError:
            print("Sem Internet, conecte e tente novamente")
            exit(0)
        return sock

def _waitMessage( udpsocket, callback ): # tupla
    global BUF_SIZE
    dprint("Thread ouvindo ... ")        
    while True:
        result = udpsocket.sock.recvfrom(BUF_SIZE)
        dprint("Data receved !")
        callback(result)        
