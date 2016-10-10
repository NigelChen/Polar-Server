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

		while True:
			gc.collect()

			# Handle the dead sockets
			if not int(len(self.deadClients)) == 0:
				for (i, u) in enumerate(self.deadClients):
					if self.deadClients[i] in self.clients:
						self.disconnect(self.deadClients[i])
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
					except: pass

					if not data:
						try: self.disconnect(_socket)
						except: continue
					else:
						try:
							parsed = json.loads(str(self.parseMessage(bytearray(data))))
							print '[Debug] '+ str(parsed)
							user.broadcast(str(self.parseMessage(bytearray(data))))
						except Exception, e:
							pass

	'''
		Initialize all the socket stuff here
	'''
	def startServer(self):
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
		self.sock.bind(('0.0.0.0', 1337))
		self.sock.listen(True)

	def disconnect(self, sock):
		self.clients[sock].died()
		del self.clients[sock]

	def handleMessage(self, user, parsedData):
		user.broadcast(parsedData)

	def handleOnline(self, user, parsedData):
		user.broadcast(parsedData)

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
