import socket, thread
import os
from subprocess import Popen, PIPE
import subprocess
import zipfile,shutil
import time
from datetime import datetime

HOST = ''           # IP address of server
PORT = 1234         # port

users = {} # dictionary structure for user access information
cdir = {} # dictionary structure for current directory of logged user
ulist = {} # dictionary structure for detection of uploading same file to same path at same time

#protocol: cmd, op1, op2
#cmd is 'opcode' (1 is register/signup; 2 is login/signin; cd, ls, mv etc)
#op1 is operand1 (user or source/destination)
#op2 is operand2: (password or destination)

def decode(msg):
    receive = msg.split()
    if len(receive)==1:
        return receive[0]
    elif len(receive)==2:
        return receive[0],receive[1]
    return receive[0],receive[1],receive[2]

def signup(receive):
    try:
        f = open("bd.txt", 'r')
    except IOError:
        print "Database file not found. Created."
        log("Database file not found. Created bd.txt",client)
    else:
        for line in f:
            (op1, op2) = line.split()
            users[op1] = op2
        f.close()
        print "Users: ",users
        if receive[1] in users:
            return -1
    with open("bd.txt","a") as f:
        f.write(receive[1]+" "+receive[2]+"\n")
    return 1

def signin(con,user):
    try:
        f = open("bd.txt", 'r')
    except IOError:
        con.send("db_nf") # Database file not found.
    else:
        for line in f:
            (op1, op2) = line.split()
            users[op1] = op2
        f.close()
    if user in users:
        con.send("ask_pwd")
        key = con.recv(1024)
        if key == users[user]:
            con.send("signin_ok")
            return 1
        else:
            con.send("wrong_pwd")
            return 0
    con.send("user_nf")
    return -1

def client2server(rpath,path,receive): # convert directory of client in a server path
    if receive[1][0]=='/': # src is an absolute path
        src = rpath+receive[1]
    else: src = os.path.join(path,receive[1])
    if len(receive)==2:
        receive = (receive[0],src)
        return receive
    if receive[2][0]=='/': # dst is an absolute path
        dst = rpath+receive[2]
    else: dst = os.path.join(path,receive[2])
    receive = (receive[0],src,dst)
    return receive

def log(logmsg,client):
    with open("log.txt","a") as log:
        log.write(str(datetime.now())+' ('+str(client[1])+'): '+logmsg+"\n")

def connected(con, client):
    print 'A connection was successfully established with', client
    con.send(str(client[1]))
    log('Connection established with '+str(client[0]),client)
    while True:
        msg = con.recv(1024)
        log('Received "'+msg+'" from client',client)
        if not msg: break
        if msg=="fin": break
        print client, msg
        receive = decode(msg)
        if receive[0]=="1":
            if(signup(receive)==1):
                print "Registered."
                log('User "'+receive[1]+'" registered',client)
                con.send("su_ok")
            else: # signup(receive)==-1
                print "User already registered."
                log('User "'+receive[1]+'" already registered"',client)
                con.send("su_nk")
        elif receive[0]=="2":
            if(signin(con,receive[1])<>1):
                print "User not logged."
                log('User "'+receive[1]+'" not logged',client)
                continue
            print "User logged."
            log('User "'+receive[1]+'" logged',client)
            rpath=os.getcwd() #root path
            path=os.path.join(rpath,receive[1]) #user path
            userlogged=receive[1]
            cdir[client[1]]=path
            if not os.path.exists(path):
                os.makedirs(path)
            msg=con.recv(1024)
            log('Received "'+msg+'" from client',client)
            receive = decode(msg)

            while receive<>'logout':
                if receive=="ls":
                    files = [f for f in os.listdir(path)]
                    for f in files:
                        print f
                        con.send(f+"   ")
                    con.send('\0') #end of transmission
                    log('Sent a list of filenames',client)

                if receive[0]=="mkdir":
                    ppath=path
                    receive = client2server(rpath,path,receive)
                    path=os.path.join(ppath,receive[1])
                    print "mkdir.path: ",path
                    if not os.path.exists(path):
                        os.mkdir(path)
                        con.send("mkdir_ok")
                        log('Created folder '+receive[1],client)
                    else:
                        con.send("mkdir_ae") #already exists
                        log('Folder '+receive[1]+' already exists',client)
                    path=ppath

                if receive[0]=="mv":
                    receive = client2server(rpath,path,receive)
                    if not (os.path.isfile(receive[2]) or os.path.isdir(receive[2])):
                        print "Error to remove: no such file or directory."
                        con.send('mv_no')
                        log('Error to move: '+receive[2]+' no such file or directory ',client)
                    else:
                        cmd = receive[0]+" "+receive[1]+" "+receive[2]
                        op = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                        output, err = op.communicate()
                        if not err:
                            print "Output:",output
                            con.send('mv_ok')
                            log('Moved '+receive[1]+' to '+receive[2],client)
                        else:
                            print "Error:",err
                            con.send('mv_no')
                            log('Error to move '+receive[1]+' to '+receive[2],client)

                if receive[0]=="rm":
                    receive = client2server(rpath,path,receive)
                    if receive[1] in cdir.values():
                        print "Another user in that directory."
                        con.send('rm_us')
                        log('Error to remove: another user connection is currently in '+receive[1],client)
                    else:
                        if not (os.path.isfile(receive[1]) or os.path.isdir(receive[1])):
                            print "Error to remove: no such file or directory."
                            con.send('rm_no')
                            log('Error to remove: '+receive[1]+' no such file or directory ',client)
                        else:
                            cmd = receive[0]+" -rf "+receive[1]
                            op = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                            output, err = op.communicate()
                            if not err:
                                #output=str(op.stdout.read())
                                print "Output:",output
                                con.send('rm_ok')
                                log('Removed '+receive[1],client)
                            else:
                                print "Error:",err
                                con.send('rm_no')
                                log('Error to remove '+receive[1],client)

                if receive[0]=="cd":
                    ppath=path
                    if receive[1]=='..': #cd ..
                        path=os.path.normpath(path+os.sep+os.pardir)
                        if os.path.exists(path):
                            cdir[client[1]]=path
                            con.send("cd2ok")
                            log('Directory changed to '+path,client)
                        else: 
                            con.send("cd2no")
                            path=ppath
                            log('Error to change directory: '+path+' not exists',client)
                    else:
                        receive = client2server(rpath,path,receive)
                        path=receive[1]
                        if os.path.isdir(path):
                            cdir[client[1]]=receive[1]
                            con.send("cd_ok")
                            log('Directory changed to '+receive[1],client)
                        else:
                            path=ppath
                            con.send("cd_nf")
                            log('Error to change directory: '+receive[1]+' not exists',client)

                if receive[0]=="upload":
                    filename=os.path.join(path,receive[1])
                    if filename in ulist.values():
                        print "Another user is uploading with this same filename to same directory."
                        con.send('up_us')
                        log('Error to upload: another user is uploading with this same filename to same directory',client)
                    else:
                        ulist[client[1]]=filename
                        con.send('up_ok')
                        with open(filename+'.zip', 'wb') as fw:
                            lenmsg = con.recv(1024) # receive file size
                            fsize = int(lenmsg)
                            print "File size to receive: ",fsize
                            rsize = 0
                            con.send("ok") # auth send
                            log('Authorized to upload file "'+filename+'" with '+lenmsg+' bytes',client)
                            while True:
                                data = con.recv(1024)
                                rsize += len(data)
                                fw.write(data)
                                if  rsize >= fsize:
                                    break
                        with zipfile.ZipFile(filename+'.zip',"r") as zip_ref:
                            zip_ref.extractall(path)
                        os.remove(filename+'.zip')
                        del ulist[client[1]] # remove uploading status from list
                        print "Upload Completed"
                        con.send('up_co')
                        log('File or directory "'+filename+'" uploaded',client)

                if receive[0]=="download":
                    receive = client2server(rpath,path,receive)
                    if (os.path.isfile(receive[1]) or os.path.isdir(receive[1])):
                        root_dir = os.path.normpath(receive[1]+os.sep+os.pardir)
                        base_dir = os.path.relpath(receive[1],root_dir)
                        con.send("down_ex") # exists
                        try:
                            shutil.make_archive('temp','zip',root_dir,base_dir)
                            fsize = os.path.getsize('temp.zip')
                            print "File size to send: ",str(fsize)
                            con.send(str(fsize)) # send file size
                            log('Sent filesize ('+str(fsize)+' bytes) to client',client)
                            msg=con.recv(2)
                            if msg=='ok': # if authorized to send then client send
                                log("Client authorized download",client)
                                with open('temp.zip','rb') as fs:
                                    data = fs.read(1024)
                                    while data:
                                        con.send(data)
                                        data = fs.read(1024)
                                print "Download completed."
                                time.sleep(0.1) # sync
                                con.send('down_ok')
                                log('File or directory "'+receive[1]+'" downloaded',client)
                            else:
                                log("Not received authorization to download",client)
                                print "Error."
                            os.remove('temp.zip')
                        except OSError: # never happens?
                            print "File or directory not found." 
                            con.send("down_nf")
                            log('File or directory to download named '+receive[1]+' not found',client)
                    else:
                        con.send("down_nf")
                        log('File or directory to download named '+receive[1]+' not found',client)

                msg=con.recv(1024)
                log('Received "'+msg+'" from client',client)
                receive = decode(msg)
            print 'User "'+userlogged+'" has logged out'
            del cdir[client[1]] # remove user connection from list
            log('User "'+userlogged+'" has logged out',client)
            # continue

    print 'Ending client connection', client
    log('Ending client connection with '+str(client[0]),client)
    con.close()
    thread.exit()

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host_port = (HOST, PORT)
tcp.bind(host_port)
tcp.listen(1)

while True:
    con, client = tcp.accept()
    thread.start_new_thread(connected, tuple([con, client]))

tcp.close()