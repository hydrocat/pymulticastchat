import threading
import socket as s
import struct
from debug import *

BUF_SIZE = 1500

class TCPSocket(object):

    def __init__(self,
                 port=0,
                 ip=''):
        
        self.ip = ip
        self.port = port
        self.sock = self.createSocket(ip,port)

    #Receba dados
    def onConnect(self, ip, port, callback):
        thread = threading.Thread(target=_onConnect,
                                  args=(self,ip,port,callback))
        thread.daemon = True
        thread.start()

    #Envie dados
    def onAccept(self, callback):
        self.sock.bind((self.ip,self.port))
        self.sock.listen(1)
        thread = threading.Thread(target=_onAccept,
                                  args=(self,callback))
        thread.daemon = True
        thread.start()

    def createSocket(self,ip,port):
        sock = s.socket(s.AF_INET, s.SOCK_STREAM)
        return sock
    
def _onAccept(tcpsock, callback):
    sock, port = tcpsock.sock.accept()
    sock.send(callback(sock=tcpsock.sock))
    dprint("Transmission ended")
    sock.close()
    tcpsock.sock.close()

def _onConnect(tcpsocket,ip,port,callback):
        try:
            tcpsocket.sock.connect((ip,port))
            while True:
                result = tcpsocket.sock.recv(BUF_SIZE)
                if len(result) == 0:
                    break
                dprint("Data receved from TCP !")
                callback(result)
            dprint("Cloding TCP connection")
            tcpsocket.sock.close()
        except ConnectionRefusedError:
            wprint("Connection to {} Refused".format(ip))
            tcpsocket.sock.close()

# fd = open("a.txt",'r')
# sock = TCPSocket(port=5656)
# #sock.onConnect("localhost", 5656, print)
# sock.onAccept(lambda:"vitorio".encode())
# print("forever")
# while True:
#     pass
