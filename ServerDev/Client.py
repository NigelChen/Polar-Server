import base64, hashlib,time

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
	def getName(self):
		return self.name
	'''
		Relays message to the client list
	'''
	def sendMessage(self, message):
		#stfu
		# if you're reading this, you're gay D:
		# some crap
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

