import socket
import select
from struct import *
import hashlib
import base64
import json
import gc
import Client

class server:


	sock = None
	clients = {}
	deadClients = []



	'''
		Checks and handles sockets connecting
	'''
	def __init__(self):
		self.startServer()
		global server
		cycle = 0


		while True:
			print '[Debug] Heartbeat #' + str(cycle) #for debugging purposes, counts each cycle
			gc.collect()

			# Handle the dead sockets
			if not int(len(self.deadClients)) == 0:
				for (i, u) in enumerate(self.deadClients):
					if self.deadClients[i] in self.clients:
						self.clients[self.deadClients[i]].died()
					del self.deadClients[i]

			# Add all the clients to the socket list
			_select = [self.sock]
			for i in self.clients:
				_select.append(i)
			read, _, error = select.select(_select, [], _select, None)
			if self.sock in error:
				self.startServer()
				continue

			for _socket in read:
				# New connection
				if _socket == self.sock:
					_client, _addr = self.sock.accept()
					self.clients[_client] = Client.Client(_client, self)
				# Handle all the users
				else:
					user = self.clients[_socket]

					try:
						data = _socket.recv(1024)
						#check if user has completed the websocket handshake
						if not user.handshake_completed:
							###websocket handshake
							headers = data
							headers = self.getSockKey(headers[headers.index(headers[headers.index('Sec-WebSocket-Key: ')+len('Sec-WebSocket-Key: '):]):].split("\r\n")[0])
							headers = "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + headers + "\r\n\r\n"
							user.usersock.send(headers)
							user.handshake_completed = True
					except: pass

					if not data:
						try: self.clients[_socket].died()
						except: continue
					else:
						try:
							parsed = json.loads(str(self.parseMessage(bytearray(data))))
							print '[Debug] '+ str(parsed)
							
							# Get the name from the user
							if parsed['type'] == "join":
								user.name = parsed['name']
								print user.name
								
								# No idea how to broadcast these types of messages from server -> client :(
								# TODO: Notify the user who all is currently in the chat room (Probably get the client to append them to the userlist)
								self.broadcast("{'message': 'Welcome to the chat server!', 'type': 'system', 'name': 'System', 'avi': 'profile.png'}")
							self.broadcast(str(self.parseMessage(bytearray(data))))
						except ValueError:
							# Typically when the user disconnects, python throws up a ValueError saying that No JSON could be decoded, so that is an indication that the user has left
							# TODO: Server notifies everyone that the user has left the chat room
							print "User has decided to disconnect, notify everyone that he left"
						except Exception, e:
							pass
			cycle +=1 #debugging purposes
	'''
		Initialize all the socket stuff here
	'''
	def startServer(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
		self.sock.bind(('0.0.0.0', 1337))

		self.sock.listen(True)

	'''
		Used to encode the websocket key to complete the handshake
	'''
	def getSockKey(self,key):
		MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
		m = hashlib.sha1(key+MAGIC)
		return base64.b64encode(m.digest())

	'''
		Broadcasts a message to every single client
	'''
	def broadcast(self, msg):
		for i in self.clients:
			for j in self.pack_message(msg):
				if isinstance(j, (int, long)):
					i.send(chr(j))
				else:
					i.send(j)

	'''
		Encode any messages to be sent to the client complying with websocket standards
	'''
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

	'''
		Unmasks any messages sent from the client to the server to be read
	'''
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
