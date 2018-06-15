import socket
import os, sys
import zipfile,shutil

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
	print("ls\ncd\nmv\nrm\nmkdir\nupload\ndownload\nlogout\n\n")

def signup(): #def signup(users):
	mode='1'
	print "Register:\n"
	username=raw_input('Insert your username: ')
	pwd=raw_input('Insert your password: ')
	tcp.send (mode+" "+username+" "+pwd)
	print "Successful\n"

def signin(): #def signin(users):
	mode='2'
	print "Login:\n"
	username=raw_input('Insert your username: ')
	tcp.send(mode+" "+username)
	msg = tcp.recv(1024)
	print "msg: ",msg
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
		print "Database file not found.\n"
	else:
		print "Username not found.\n"
	return 0

def ls():
	i=0
	tcp.send("ls")
	files = tcp.recv(32)
	while not files.endswith("\0"): files += tcp.recv(32)
	print files
	return 1

# main
mode=start_menu()
while mode <> 'exit':
	op='0'
	path="/"
	if mode=="1":
		signup()
	elif mode=="2":
		logged=signin()
		print "logged: ",logged
		if (op[0]=='logout'):
			tcp.send("logout")
		if logged:
			path=logged[1]
			rpath=path
		while( logged and (op[0]<>'logout') ):			
			ppath=path #previous path
			print "path: ",path
			# if not os.path.exists(path):
			# 	os.makedirs(path)
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
				if len(op)==1:
					print "Invalid operand."
					continue
				elif op[1]=='..':
					if path==rpath:
						print "Can't."
						continue
				tcp.send(op[0]+" "+op[1])
				msg = tcp.recv(5)
				if msg=='cd_nf':
					print "Directory not found."
				elif msg=='cd_ok':
					path=os.path.join(path,op[1])
					print "Cd Success."
				elif msg=='cd2ok':
					path=os.path.normpath(path+os.sep+os.pardir) #retrocede uma pasta
					print "Cd.. Success."
				else: #cd2no
					pass
			elif op[0]=='ls':
				ls()
			elif op[0]=='mkdir':
				if len(op)==1:
					print "Invalid operand."
					continue
				tcp.send(op[0]+" "+op[1])
				msg = tcp.recv(8)
				if msg=='mkdir_ae':
					print "Already exists."
				else:
					print "Created."
			elif op[0]=='mv':
				if len(op)<3:
					print "Invalid operand."
					continue
				tcp.send(op[0]+" "+op[1]+" "+op[2])
				msg = tcp.recv(5)
				if msg=='mv_ok':
					print "Moved."
				else:
					print "Error."
			elif op[0]=='rm':
				if len(op)==1:
					print "Invalid operand."
					continue
				tcp.send(op[0]+" "+op[1])
				msg = tcp.recv(5)
				if msg=='rm_ok':
					print "Removed."
				else:
					print "No such file or directory."

			elif op[0]=='upload':
				if len(op)==1:
					print "Invalid operand."
					continue
				tcp.send(op[0]+" "+op[1])

				print "atual: ",os.getcwd()

				root_dir = os.path.normpath(op[1]+os.sep+os.pardir)
				base_dir = os.path.relpath(op[1],root_dir)
				##base_dir=os.path.basename(path) retorna nome arq/pasta
				try:
					shutil.make_archive('temp','zip',root_dir,base_dir)


					fsize = os.path.getsize('temp.zip')
					print "fsize: ",str(fsize)
					tcp.send(str(fsize)) # envia tamanho
					msg=tcp.recv(2)
					if msg=='ok': # se autorizado a enviar, envia
						with open('temp.zip','rb') as fs:
							data = fs.read(1024)
							while data:
								tcp.send(data)
								data = fs.read(1024)
						print "Upload completed."
					else: print "Error."

					os.remove('temp.zip')

				except OSError:
					print "File or directory not found."
					continue


			elif op[0]=='download':
				if len(op)==1:
					print "Invalid operand."
					continue
				tcp.send(op[0]+" "+op[1])

				print "atual: ",os.getcwd()

				with open('temp.zip', 'wb') as fw:
					msgtam = tcp.recv(1024) #recebe tam arquivo
					fsize = int(msgtam)
					print "fsize: ",fsize
					rsize = 0
					tcp.send("ok") #autoriza receber
					while True:
						data = tcp.recv(1024)
						rsize += len(data)
						fw.write(data)
						if  rsize >= fsize:
							break
					print "Download Completed"
				msg = tcp.recv(7)
				print "msg_down: ",msg

				with zipfile.ZipFile('temp.zip',"r") as zip_ref:
					zip_ref.extractall()

				os.remove('temp.zip')

				if msg=='down_ok':
					print "Sucess."
				else:
					print "File or directory not found."


			else: print "Invalid operand. See help."


	mode=start_menu()


tcp.send("fin")
tcp.close()

# base_dir = '/bla/bing'
# filename = 'data.txt'
# os.path.join(base_dir, filename)




# while True:
#     data = s.recv(1024)

#     if not data: print " Done "; break

#     recvd += data



# import shutil
# file_to_zip = 'test.txt'            # file to zip
# target_path = 'C:\\test_yard\\'     # dir, where file is

# try:
#     shutil.make_archive('archive', 'zip', target_path, file_to_zip)
# except OSError:
#     pass



# shutil.make_archive('nome','zip','/home/luisfernando/Documents/TD/trab1/','diretorio')


					# saved_path = os.getcwd()
					# os.chdir(new_path)
					# try:
					#     # code that does stuff in new_path goes here
					# finally:
					#     os.chdir(saved_path)