import base64, hashlib

class Client:

	'''
		Initializes information on the client
	'''
	def __init__(self, usersock, parent):
		self.usersock = usersock
		self.parent = parent
		self.handshake_completed = False

	'''
		Relays message to the client list
	'''
	def sendMessage(self, message):
		self.parent.broadcast(message)


	'''
		Deletes self from the client list when it is disconnected.
		Has to be called by the server to work.
	'''
	def died(self):
		try:
			self.usersock.close()
			print "Disconnected the client"
		finally:
			# TODO: Store user names so that way people can know who disconnected
			del self.parent.clients[self.usersock]
			msg = '{"type": "message", "body": "disconnected", "name": "system"}'
			self.parent.broadcast(msg)

