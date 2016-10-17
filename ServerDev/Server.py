import socket
import select
from struct import *
import hashlib
import base64
import json
import gc
import Client
from urllib import quote




#properties:
# - The server will kick out the client if the server detects that the client tampered with the client-side code if the client breaks protocol
# - Any special characters sent to the server will automatically be turned into HTML entities. 


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
				send = True
				# New connection
				if _socket == self.sock:
					_client, _addr = self.sock.accept()
					self.clients[_client] = Client.Client(_client, self)
				# Handle all the users
				else:
					user = self.clients[_socket]

					try:

						data = _socket.recv(1024)
						print '[Debug] length of data: ' + str(len(data))
						#check if user has completed the websocket handshake
						if not user.handshake_completed:
							###websocket handshake
							headers = data
							headers = self.getSockKey(headers[headers.index(headers[headers.index('Sec-WebSocket-Key: ')+len('Sec-WebSocket-Key: '):]):].split("\r\n")[0])
							headers = "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + headers + "\r\n\r\n"
							user.usersock.send(headers)
							data = None
							user.handshake_completed = True
					except: pass

					if not data or len(data) <=1:
						#The tested case(s) when this happens:
						#1) When a user just completes a handshake
						print '[Debug] NO DATA PASSED: PASS'
						pass 
					else:
						try:
							#NOTE FOR CLIENT REPO: The server will escape certain characters into HTML entities to prevent XSS.
							#it will be the client's responsibility to escape the HTML entities SAFELY.
							parsed = json.loads(str(self.parseMessage(bytearray(data))))
							print '[Debug] '+ str(parsed)
							
							for i in parsed:
								#NOTE FOR CLIENT REPO: max message length is 256 characters while the avatar, names, etc. max length is 32 characters long
								#if breaks rules, then the server kicks out the user, indicating that the client tampered with client-side code.
								if len(parsed[i]) > 32 or (i == "message" and len(parsed[i]) > 256): 
									print '[Debug] DISCONNECTED CLIENT FOR BREAKING PROTOCOL'
									self.kick(_socket)
									parsed['type'] = "ERROR"
									continue

							# Get the name from the user
							if parsed['type'] == "join":
								self.send_to_client('{"message": "Welcome to the chat server!", "type": "system", "name": "System", "avi": "profile.png"}', self.clients[_socket])
								onlineUsers = []
								#NOTE FOR CLIENT REPO: Client will NEED to parse the following user format in the "message" field...
								#ex) "name,alice,bob"
								for i in self.clients:
									onlineUsers.append(self.clients[i].getName())
								data = {}
								data['message'] = ",".join(onlineUsers)
								data['type'] = 'onSet'
								data['name'] = 'System'
								data['avi'] = 'n/a'
								json_data = json.dumps(data)
								self.send_to_client(str(json_data), self.clients[_socket])

		
							dataz = {}
							for i in parsed:
								#for nitin:
								
								ayy = parsed[i]
								dataz[i] = quote(ayy.encode('utf-8')) #quote() to escape any HTML entities just incase
							json_data = json.dumps(dataz)
							self.broadcast(str(json_data))
						except ValueError:
							#The cases where this will activate:
							#1) unformatted JSON packets are sent
							#2) a user disconnects
							self.kick(_socket)
						
			cycle +=1 #debugging purposes
	'''
		Kicks a user off the server
	'''
	def kick(self,c):
		tempname = self.clients[c].getName()
		self.clients[c].died()
		self.broadcast(str(json.dumps({'message':tempname,
			'type':'leave',
			'name':'System',
			'avi':'profile.png'})))

	'''
		Sends a message to a specific user
		takes in a client handler and a message
	'''
	def send_to_client(self,msg,client):
		for j in self.pack_message(msg):
			if isinstance(j, (int, long)):
				client.usersock.send(chr(j))
			else:
				client.usersock.send(j)
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
