import socket
HOST = '127.0.0.1'     # Endereco IP do Servidor
PORT = 5000            # Porta que o Servidor esta
tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
dest = (HOST, PORT)
tcp.connect(dest)

#cod_msg = {200:ask_pwd}

def start_menu():
	print "\nWelcome to UnBox!\n"
	mode=raw_input("1.signin\n2.signup\nexit\n\n")
	return mode

def help():
	print "Commands avaliable:\n"
	op=raw_input("ls\ncd\nmv\nrm\nmkdir\nupload\ndownload\nlogout\n\n")
	return op

def signup(): #def signup(users):
	mode='1'
	print "Register:\n"
	username=raw_input('Insert your username: ')
	pwd=raw_input('Insert your password: ')
	tcp.send (mode+" "+username+" "+pwd+"\n")
	print "Successful\n"

def signin(): #def signin(users):
	mode='2'
	pwd='-'
	print "Login:\n"
	username=raw_input('Insert your username: ')
	tcp.send(mode+" "+username+" "+pwd+"\n")
	msg = tcp.recv(1024)
	if msg=="ask_pwd":
		msg=raw_input("Insert your password: ")
		tcp.send(msg)
		msg = tcp.recv(1024)
		if msg=="signin_ok":
			print "Login successful.\n"
			return 1
		else:
			print "Wrong password.\n"
	elif msg=="db_nf":
		print "Database file not found.\n"
	else:
		print "Username not found.\n"
	return 0




# main
mode=start_menu()
op='0'
while mode <> 'exit':
	if mode=="1":
		signup()
	elif mode=="2":
		si=signin()
		while( si and (op<>'logout') ):
			op=help()
	mode=start_menu()


tcp.send("fin")
tcp.close()