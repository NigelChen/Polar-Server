import Server, Client

try:
	print "Starting up Polar Chat"
	server = Server.server()
except KeyboardInterrupt:
	print "Shutting down server..\n"