import base64, hashlib

class Client:

	def __init__(self, usersock, parent):
		self.usersock = usersock
		self.parent = parent

		headers = usersock.recv(1024)
		headers = self.getSockKey(headers[headers.index(headers[headers.index('Sec-WebSocket-Key: ')+len('Sec-WebSocket-Key: '):]):].split("\r\n")[0])
		headers = "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: " + headers + "\r\n\r\n"
		usersock.send(headers)

	def getSockKey(self,key):
		MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
		m = hashlib.sha1(key+MAGIC)
		return base64.b64encode(m.digest())

	def broadcast(self, msg):
		for i in self.parent.clients:
			for j in self.parent.pack_message(msg):
				if isinstance(j, (int, long)):
					i.send(chr(j))
				else:
					i.send(j)

	def sendMessage(self, message):
		self.broadcast(message)


	# Might need to clean this method up
	def died(self):
		try:
			self.usersock.close()
			print "Disconnected the client"
		finally:
			msg = '{"type": "message", "body": "disconnected", "name": "system"}'
			for i in self.parent.clients:
				try:
					if i != self.usersock:
						for j in self.parent.pack_message(msg):
							if isinstance(j, (int, long)):
								i.send(chr(j))
							else:
								i.send(j)
				except Exception, e:
					print e

