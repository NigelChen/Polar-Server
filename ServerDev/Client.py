import base64, hashlib

class Client:
	# Stores the name of the user in this variable
	name = ""

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
		# if you're reading this, you're gay D:
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
			del self.parent.clients[self.usersock]
			msg = '{"type": "message", "body": "disconnected", "name": "system"}'
			self.parent.broadcast(msg)

