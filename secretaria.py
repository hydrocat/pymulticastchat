 #Implementa o protocolo dado
import time 
import udpSocket
import tcpSocket
from debug import *
import re
from os import listdir, stat
from os.path import isdir, join
LEAVE_TIMEOUT = 1

# MCAST_GROUP = "225.1.2.3"
# MCAST_PORT  = 6789

# UNICAST_PORT = 6799
MCAST_GROUP = "225.1.2.3"
MCAST_PORT  = 5566

UNICAST_PORT = 5555

BUF_SIZE = 1000

regexes = [
    re.compile(
        r"(?P<cmd>JOIN(ACK)?|LISTFILES|LEAVE) \[(?P<apelido>.*)\]"),
    re.compile(
        r"(?P<cmd>MSG) \[(?P<apelido>.*)\] (?P<msg>.*)"),
    re.compile(
        r"(?P<cmd>MSGIDV FROM) \[(?P<de>.*)\] TO \[(?P<para>.*)\] (?P<msg>.*)"),
    re.compile(
        r"(?P<cmd>FILES) \[(?P<filenames>(.*(, .*)*)?)\]"),
    re.compile(
        r"(?P<cmd>DOWNFILE) \[(?P<apelido>.*)\] (?P<filename>.*)"),
    re.compile(
    r"(?P<cmd>DOWNINFO) \[(?P<filename>[^,]+), (?P<size>\d+), (?P<ip>\d+(.\d+){3}), (?P<porta>\d+)\]")
    ]

templates = {
    "JOIN" : "JOIN [{}]",
    "JOINACK" : "JOINACK [{}]",
    "MSG" : "MSG [{}] {}",
    "MSGIDV FROM" : "MSGIDV FROM [{}] TO [{}] {}",
    "LISTFILES" : "LISTFILES [{}]",
    "FILES": "FILES [{}]",
    "DOWNFILE": "DOWNFILE [{}] {}",
    "DOWNINFO": "DOWNINFO [{}, {}, {}, {}]",
    "LEAVE" : "LEAVE [{}]"
}

#Comes through multicast
def recv_join(secretaria, match, addr):
    print("{} Joined.".format(match.group('apelido')))
    secretaria.addContact(match.group('apelido'), addr)
    secretaria.sendUnicast("JOINACK", match.group('apelido'), secretaria.nickname)

def recv_joinack(secretaria, match, addr):
    dprint("Add contact {} from {}".format(match.group('apelido'), addr))
    secretaria.addContact(match.group('apelido'), addr)

def recv_msg(secretaria, match, addr):
    print("{} diz: {}".format(match.group('apelido'),
                              match.group('msg')))

def recv_leave(secretaria, match, addr):
    dprint("Removing contact {}".format(match.group('apelido')))
    secretaria.contacts.pop(match.group('apelido'))


#Comes through unicast
def recv_msgidv(secretaria, match, addr):
    print("_{}_ diz: {}".format(match.group('de'),
                                match.group('msg')))
    
def recv_listfiles(secretaria, match, addr):
    files = ", ".join([x for x in listdir(secretaria.filedir) if not isdir(x)])
    secretaria.sendUnicast("FILES", match.group('apelido'), files)
    
def recv_files(secretaria, match, addr):
    contact = ""
    for name in secretaria.contacts:
        if secretaria.contacts[name] == addr[0]:
            contact = name
            break
    print("{} tem os arquivos: {}".format(contact, match.group('filenames')))

    
def recv_downfile(secretaria, match, addr):
    filename = match.group('filename')
    fileContents = open(join(secretaria.filedir,filename), 'rb').read()
    sock = tcpSocket.TCPSocket()
    sock.onAccept(lambda sock: fileContents )
    secretaria.sendUnicast("DOWNINFO",
                           secretaria.nickname,
                           filename,
                           stat( join(secretaria.filedir,filename)).st_size,
                           secretaria.contacts[secretaria.nickname],
                           sock.sock.getsockname()[1]
    )
    
def recv_downinfo(secretaria, match, addr):
    filename = "download-" + match.group('filename')
    f = open(join(secretaria.filedir,filename),'wb')
    sock = tcpSocket.TCPSocket()
    sock.onConnect(match.group('ip'),
                   int( match.group('porta') ),
                   f.write
                   )

recv_functions = {
    "JOIN" : recv_join,
    "JOINACK" : recv_joinack,
    "MSG" : recv_msg,
    "MSGIDV FROM" : recv_msgidv,
    "LISTFILES" : recv_listfiles,
    "FILES": recv_files,
    "DOWNFILE": recv_downfile,
    "DOWNINFO": recv_downinfo,
    "LEAVE" : recv_leave
}

MULTICAST_COMMANDS = ["JOIN", "MSG", "LEAVE"]
UNICAST_COMMANDS = ["JOINACK"  , "MSGIDV FROM",
                    "LISTFILES", "FILES",
                    "DOWNINFO" , "DOWNFILE" ]

boss_commands = [
    re.compile(r"(?P<cmd>\@)(?P<apelido>.*) (?P<msg>.*)"),
    re.compile(r"(?P<cmd>!)(?P<apelido>.*) !(?P<nomearquivo>.*)"),
    re.compile(r"(?P<cmd>\?)"),
    re.compile(r'(?P<cmd>\*)(?P<apelido>.*)')
]

def send_listfile(secretaria, match):
    secretaria.sendUnicast("LISTFILES",
                           match.group('apelido'),
                           secretaria.nickname)
    
def send_msgidv(secretaria, match):
    secretaria.sendUnicast("MSGIDV FROM",
                           match.group('apelido'),
                           secretaria.nickname,
                           match.group('apelido'),
                           match.group('msg'))

def send_downfile(secretaria, match):
    secretaria.sendUnicast("DOWNFILE",
                           match.group('apelido'),
                           match.group('apelido'),
                           match.group('nomearquivo'))

def show_contacts(secretaria, match):
    print(secretaria.contacts)
    
send_functions = {
    '*': send_listfile,
    '@': send_msgidv,
    '!': send_downfile,
    '?': show_contacts
}
class Secretaria(object):
    def __init__(self, nickname, filedir):
        self.nickname = nickname
        self.filedir = filedir
        self.multicast = udpSocket.MulticastUDPSocket(MCAST_PORT,
                                                      MCAST_GROUP,
                                                      ip = MCAST_GROUP,
            callback = self.MessageCallbackFactory(MULTICAST_COMMANDS,debug="MCast"))
        
        self.unicast = udpSocket.UDPSocket(UNICAST_PORT,    
            callback = self.MessageCallbackFactory(UNICAST_COMMANDS, debug="Unicast"))
 
        self.contacts = {}
        msg = templates["JOIN"].format(self.nickname).encode()
        self.multicast.send(msg)

    def leaveGroup(self):
        self.sendMulticast("LEAVE", self.nickname)
        time.sleep(LEAVE_TIMEOUT)
          
    def addContact(self,name, addr):
        dprint("User added:{}".format(name))
        self.contacts[name] = addr[0]
        
    def sendMulticast(self, cmd, *params):
        dprint("Sending Multicast cmd {} with params {} ".format(cmd,*params))
        msg = templates[cmd].format(*params).encode()
        self.multicast.send(msg)

    def sendUnicast(self, cmd, contact, *params):
        dprint("Sending Unicast cmd {} to {} with {} params".format(cmd, contact, *params))
        msg = templates[cmd].format(*params).encode()
        self.unicast.send(msg, self.contacts[contact], UNICAST_PORT)

    def MessageCallbackFactory(self, accept, debug=""):
        def callback( data ):
            msg, addr = data
            msg = msg.decode()
            dprint("{} Message Received: {}".format(debug, msg))
            try:
                match = getMatch(msg)
                if match.group('cmd') in accept:
                    recv_functions[match.group('cmd')](self, match, addr)
                else:
                    wprint("{} Bad message Received, Not in accpet ".format(debug))
            except IndexError:
                wprint("{} Bad message received\n{}".format(debug, data))
        return callback
    
    def attendRequest(self, message ):
        sprint(message)
        try:
            match = getCmdMatch( message )
            send_functions[match.group('cmd')](self, match)
        except IndexError:
            self.sendMulticast("MSG", self.nickname, message)
            
        
        
#Raises IndexError if the message ain't good
def getMatch( msg ):
    return list(filter(None,(x.search(msg) for x in regexes)))[0]
def getCmdMatch( msg ):
    return list(filter(None,(x.search(msg) for x in boss_commands)))[0]
# s = Secretaria("vitorio", "/home/hydrocat/SD/chat")

# try:
#     while True:
#         sprint(s.contacts)
# #        s.sendMulticast("MSG",*(s.nickname,("teste")))
#         time.sleep(2)
#         s.sendUnicast("LISTFILES",s.nickname, s.nickname)
#         time.sleep(2)
#         s.sendUnicast("DOWNFILE",s.nickname, s.nickname, "main.py")

        
# except KeyboardInterrupt:
#     s.leaveGroup()
