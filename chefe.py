from secretaria import *
import re
from debug import *
# @nome -> envia msg privada para nome
# *nome -> lista os arquivos de nome
# !nome !arquivo -> baixa o arquivo de nome
s = Secretaria("vitorio2", "/home/hydrocat/Downloads")

try:
    while True:
        s.attendRequest( input() )
except KeyboardInterrupt:
    s.leaveGroup()

