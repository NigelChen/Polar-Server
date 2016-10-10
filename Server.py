import socket
import hashlib,base64
import threading
import sys
from struct import *
import time
import json
import asyncore
clients = []
userlist = []

'''
CLIENT HANDLER
has functionality to write/read client messages
'''
class Handler(asyncore.dispatcher):

    #init
    def __init__(self,socket,server):
        self.buffer = ''
        self.server = server

        ###HTTP WEBSOCKET HANDSHAKE
        headers = socket.recv(1024)
        headers = self.getSockKey(headers[headers.index(headers[headers.index('Sec-WebSocket-Key: ')+len('Sec-WebSocket-Key: '):]):].split("\r\n")[0])
        headers = "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + headers + "\r\n\r\n"
        socket.send(headers)



        asyncore.dispatcher.__init__(self, socket)

    #Sends any incoming messages to the server to handle
    def handle_read(self):
        msg = self.recv(1024)
        if msg:
            self.server.income_msg(self,msg)
    #Used for encoding the sock key from http headers. Only used for websocket handshake
    def getSockKey(self,key):
        MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        m = hashlib.sha1(key+MAGIC)
        return base64.b64encode(m.digest())
    #Used by the driver to send messages
    def justsend(self,msg):
        self.send(msg)
'''
THE SERVER
accepts, collects/handles messages from clients
'''
class WebServer(asyncore.dispatcher):

    #used to encode any messages for sending through websocket to
    #comply with websocket standards
    def pack_message(self,msg):
        payload = []
        payload.append(129)
        if(len(msg) < 126):
            payload.append(len(msg))
        elif len(msg) >= 126:
            payload.append((126))
            payload.append(pack("!H",len(msg)))
        payload.append(msg)
        return payload

    #unmasks a message sent from the client.
    def parseMessage(self,msg):
        startIndex = 2
        if (msg[1]&127) == 126:
            startIndex = 4
        elif (msg[1]&127) == 127:
            startIndex = 10
        ns = msg[startIndex:startIndex+4]
        a = 0
        decoded = bytearray()
        for i in range(startIndex+4,len(msg)):
            msg[i]
            ns[a%4]
            decoded.append(msg[i]^ns[a%4])
            a=a+1
        return decoded

    #init
    def __init__(self,host,port):
        asyncore.dispatcher.__init__(self)
        self.clients = [] #all client handler instances
        self.names = [] #names of all clients connected
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host,port))
        self.listen(10) #MAX = 10


    #accepts any incoming clients
    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock,addr = pair
            print 'NEW CLIENT CONNECTED'
            #sends accepted clients to async handler
            handler = Handler(sock,self)
            self.clients.append(handler)

    #handles any incoming messages from the handlers(clients)
    def income_msg(self,handle,msg):
        #messages are sent in this JSON format:
        # {"type":"mesage","body":"Hello World!!!","name":"Bob"}
        #online notifications are sent in this JSON format:
        # {"type":"online","name":"Alice"}
        parsed = json.loads(str(self.parseMessage(bytearray(msg))))
        if parsed['type'] == 'message':
            self.broadcast(self.parseMessage(bytearray(msg)))
        elif parsed['type'] == 'online':
            self.broadcast(self.parseMessage(bytearray(msg)))

    #broadcasts a message to all clients
    def broadcast(self,msg):
        for i in self.clients:
            for j in self.pack_message(msg):
                if isinstance( j, ( int, long ) ):
                    i.justsend(chr(j))
                else:
                    i.justsend(j)

WebServer('localhost',1337) #ws://localhost:1337
asyncore.loop()
