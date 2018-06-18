import socket
import os
import zipfile,shutil

def start_menu():
	print "\nWelcome to UnBox!\n"
	cmd=raw_input("1. Sign up\n2. Sign in\n   exit\n\n> ")
	return cmd

def help():
	print "Commands avaliable:\n"
	print("ls\ncd <dst>\nmv <src> <dst>\nrm <src>\nmkdir <src>")
	print("upload <file or folder>\ndownload <file or folder>\nlogout\n")

def signup():
	cmd='1'
	print "Register:\n"
	username=raw_input('Insert your username: ')
	pwd=raw_input('Insert your password: ')
	tcp.send (cmd+" "+username+" "+pwd)
	msg = tcp.recv(5)
	if msg=="su_ok":
		print "Successful\n"
	else: print "User already registered."

def signin():
	cmd='2'
	print "Login:\n"
	username=raw_input('Insert your username: ')
	tcp.send(cmd+" "+username)
	msg = tcp.recv(1024)
	if msg=="ask_pwd":
		msg=raw_input("Insert your password: ")
		tcp.send(msg)
		msg = tcp.recv(1024)
		if msg=="signin_ok":
			print "Login successful.\n"
			return 1,username
		else:
			print "Wrong password.\n"
	elif msg=="db_nf":
		print "Database file not found. Please create an account first.\n"
	else:
		print "Username not found.\n"
	return 0

def ls():
	tcp.send("ls")
	files = tcp.recv(32)
	while not files.endswith("\0"): files += tcp.recv(32)
	print files
	return 1

# main
HOST = '127.0.0.1'	# IP address of server
PORT = 1234	# Port
tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_port = (HOST, PORT)
tcp.connect(host_port)
client = tcp.recv(128)
shared=[] # list structure for shared folders information
cmd=start_menu()
while cmd <> 'exit':
	op=' '
	path="/"
	if cmd=="1":
		signup()
	elif cmd=="2":
		logged=signin()
		if (op[0]=='logout'):
			tcp.send("logout")
		if logged:
			path='/'+logged[1]
			rpath=path
		while( logged and (op[0]<>'logout') ):			
			sh=0
			ppath=path #previous path
			op=raw_input(path+"> ")
			op = op.split()
			if len(op)==0:
				op=' '
				continue

			if op[0]=='logout':
				print op[0]
				tcp.send("logout")

			if op[0]=='help':
				help()

			elif op[0]=='cd':
				if len(op)<>2:
					print "Invalid operand."
					continue
				print "op1:",op
				if op[1].split(':')[0]=='sh':
					sh=1

				if op[1][0] == '/' and not sh:
					if '/'+op[1].split('/')[1]<>rpath:
						print "Absolute path must be started from "+rpath
						continue
				elif op[1]=='..':
					print "path..:",os.path.normpath(path+os.sep+os.pardir)
					if path==rpath: 
						print "Can't."
						continue

				tcp.send(op[0]+" "+op[1])
				msg = tcp.recv(5)
				if msg=='cd_nf':
					print "Directory not found."
				elif msg=='cd_ok':
					if sh:
						path=op[1]
						continue
					path=os.path.join(path,op[1])
				elif msg=='cd2ok':
					path=os.path.normpath(path+os.sep+os.pardir) # returns one directory
				elif msg=='cd2ns':
					if op[1]=='..':
						print "path:",path
						print os.path.normpath(path+os.sep+os.pardir)+" isn't a shared folder!"
						continue
					print op[1]+" isn't a shared folder!"
				else: #cd2no
					pass


			elif op[0]=='ls':
				if len(op)<>1:
					print "Invalid operand."
					continue
				ls()

			elif op[0]=='mkdir':
				if len(op)<>2:
					print "Invalid operand."
					continue
				if op[1][0] == '/':
					if '/'+op[1].split('/')[1]<>rpath:
						print "Absolute path must be started from "+rpath
						continue
				tcp.send(op[0]+" "+op[1])
				msg = tcp.recv(8)
				if msg=='mkdir_ae':
					print "Already exists."
				else:
					print "Created."

			elif op[0]=='mv':
				if len(op)<>3:
					print "Invalid operand."
					continue
				if op[1][0] == '/':
					if '/'+op[1].split('/')[1]<>rpath:
						print "Absolute path must be started from "+rpath
						continue
				if op[2][0] == '/':
					if '/'+op[2].split('/')[1]<>rpath:
						print "Absolute path must be started from "+rpath
						continue
				tcp.send(op[0]+" "+op[1]+" "+op[2])
				msg = tcp.recv(5)
				if msg=='mv_ok':
					print "Moved."
				else:
					print "Error."

			elif op[0]=='rm':
				if len(op)<>2:
					print "Invalid operand."
					continue
				tcp.send(op[0]+" "+op[1])
				msg = tcp.recv(5)
				if msg=='rm_ok':
					print "Removed."
				elif msg=='rm_us':
					print "Another user in that directory."
				else:
					print "No such file or directory."

			elif op[0]=='upload':
				if len(op)<>2:
					print "Invalid operand."
					continue

				if not (os.path.isfile(op[1]) or os.path.isdir(op[1])):
					print "No such file or directory."
					continue

				root_dir = os.path.normpath(op[1]+os.sep+os.pardir)
				base_dir = os.path.relpath(op[1],root_dir) 
				# base_dir = os.path.basename(op[1]) # another way to find base_dir (problem if terminated with '/')
				tcp.send(op[0]+" "+base_dir)
				
				print base_dir
				msg = tcp.recv(5)
				if msg=='up_us':
					print "Another user is uploading with this same filename to same directory."
					continue
				else:
					try:
						shutil.make_archive(base_dir+client,'zip',root_dir,base_dir)
						fsize = os.path.getsize(base_dir+client+'.zip')
						tcp.send(str(fsize)) # send file size
						msg=tcp.recv(2)
						if msg=='ok': # if authorized to send then send
							with open(base_dir+client+'.zip','rb') as fs:
								data = fs.read(1024)
								while data:
									tcp.send(data)
									data = fs.read(1024)
						else: print "Error."
						os.remove(base_dir+client+'.zip')
					except OSError:
						print "File or directory not found."
						continue
					msg = tcp.recv(5)
					if msg=='up_co':
						print "Upload completed."


			elif op[0]=='download':
				if len(op)<>2:
					print "Invalid operand."
					continue
				tcp.send(op[0]+" "+op[1])
				base_dir = os.path.basename(op[1])
				msg=tcp.recv(7)
				if msg=='down_ex':
					with open(base_dir+client+'.zip', 'wb') as fw:
						msgtam = tcp.recv(1024) # receive file size
						fsize = int(msgtam)
						rsize = 0
						tcp.send("ok") # authorizes to send
						while True:
							data = tcp.recv(1024)
							rsize += len(data)
							fw.write(data)
							if  rsize >= fsize:
								break
					msg = tcp.recv(7)
					with zipfile.ZipFile(base_dir+client+'.zip',"r") as zip_ref:
						zip_ref.extractall()
					os.remove(base_dir+client+'.zip')
				else:
					print "File or directory not found."
					continue
				if msg=='down_ok':
					print "Download Completed."
				else:
					print "File or directory not found."

			elif op[0]=='share': # share a folder to another users can access
				shared.append(path)
				tcp.send("share")
				print "shared:",shared

			else: print "Invalid command. See help."

	cmd=start_menu()

tcp.send("fin")
tcp.close()