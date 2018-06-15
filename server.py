import socket, thread
import os, sys
from subprocess import Popen, PIPE
import subprocess
import zipfile,shutil

HOST = ''              # Endereco IP do Servidor
PORT = 5000            # Porta que o Servidor esta

users = {}

#protocolo: cmd, op1, op2
#cmd eh comando (1 eh cadastro, 2 eh login ...)
#op1 pode ser: usuario, origem
#op2 pode ser: senha, destino

def decode(msg):
    receive = msg.split()
    #(cmd,op1,op2) = msg.split()
    if len(receive)==1:
        print "decode.tamanho 1"
        return receive[0]
    elif len(receive)==2:
        return receive[0],receive[1]

    print "decode.tamanho 3"
    return receive[0],receive[1],receive[2]

def signup(receive): #def signup(users):

    with open("bd.txt","a") as f:
        f.write(receive[1]+" "+receive[2]+"\n")
    #print 'sucesso\n'
    return 1

def signin(con,user): #def signin(users):
    try:
        f = open("bd.txt", 'r')
    except IOError:
        #print 'O BD nao existe'
        con.send("db_nf")
    else:
        for line in f:
            (op1, op2) = line.split()
            users[op1] = op2
        f.close()
    if user in users:
        con.send("ask_pwd")
        #key = raw_input('Informe a senha: ')
        key = con.recv(1024)
        if key == users[user]:
            con.send("signin_ok")
            return 1
        else:
            con.send("wrong_pwd")
            return 0
    con.send("user_nf")
    return -1

def console(cmd):
    p = Popen(cmd, shell=True, stdout=PIPE)
    out, err = p.communicate()
    return (p.returncode, out, err)

def conectado(con, cliente):
    print 'A connection was successfully established with', cliente

    while True:
        print "\n\nInicio"
        msg = con.recv(1024)
        if not msg: break
        if msg=="fin": break
        print cliente, msg
        receive = decode(msg)
        print "receive1: ",receive

        if receive[0]=="1":
            signup(receive)
        elif receive[0]=="2":
            if(signin(con,receive[1])<>1):
                print "Usuario nao logou"
                continue



# >>> rpath#### isso sera o rpath= os.getcwd
# '/home/luisfernando/Documents/TD/trab1/servidor'
# >>> relpath
# 'luis/aa'
# >>> os.path.join(rpath,relpath)
# '/home/luisfernando/Documents/TD/trab1/servidor/luis/aa'


# IMPORTANTE: FAZER NUNCA ENTRAR EM NENHUMA PASTA. FAZER RPATH SER
# ONDE ESTA O SERVER.PY
# FAZER FUNCIONAR DIRETORIO RELATIVO E ABSOLUTO
# DICA: FAZER EQUIVALENCIA DE DIRETORIO SEMPRE E USAR SEMPRE O ABSOLUTO
# O QUE PENSEI: EU SEMPRE SEI O ENDERECO RELATIVO (/luis/aa etc)
# TAMBEM SEMPRE SEI O RPATH
# CASO O USUARIO SEMPRE DER O ABSOLUTO (lado cliente), seria so fazer join
# como tambem eh pra aceitar relativo, verificar se eh relativo
# se relativo, juntar rpath+root_dir+end_relativo
# root_dir eh a subtracao (path - relativo) e rpath
#>>parentpath=os.path.normpath(path+os.sep+os.pardir)
#>>root_dir=os.path.relpath(parentpath,rpath)

# ex: path eh /servidor/luis/aa e rpath eh /servidor
# root_dir = /luis
# root_dir seria o os.path.relpath(path,rpath)
# se o usuario mandar relativo, e eu tenho path, so fazer o join dos 3
# se o usuario mandar absotulo

            rpath=os.getcwd() #root path
            path=os.path.join(rpath,receive[1]) #user path
            relpath=receive[1]

            #print "path: ",path
            if not os.path.exists(path):
                os.makedirs(path)
            #os.chdir(upath)
            msg=con.recv(1024)
            receive = decode(msg)
            print "receive2: ",receive
            while receive<>'logout':
                #print 'inicio.path: ',path
                if receive=="ls":
                    print "ls.path: ",path
                    files = [f for f in os.listdir(path)]
                    #print "files: ",files
                    #print "f: ",f
                    for f in files:
                        print f
                        con.send(f+"   ")
                    con.send('\0') #end of transmission
                if receive[0]=="mkdir":
                    ppath=path
                    path=os.path.join(ppath,receive[1])
                    print "mkdir.path: ",path
                    if not os.path.exists(path):
                        os.mkdir(path)
                        con.send("mkdir_ok")
                    else: con.send("mkdir_ae") #already exists
                    path=ppath
                if receive[0]=="mv":
                    print "path: ",path
                    print "atual: ",os.getcwd()
                    print "receive[2]: ",receive[2]
                    print "rpath+receive[2]: ",rpath+receive[2]
                    cmd = receive[0]+" "+receive[1]+" "+receive[2]
                    if receive[2][0]=='/':
                        dire=rpath+receive[2]
                        cmd = receive[0]+" "+receive[1]+" "+dire
                    print cmd
                    os.chdir(path)

                    op = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                    output, err = op.communicate()
                    if not err:
                        #output=str(op.stdout.read())
                        print "Output:",output
                        con.send('mv_ok')
                    else:
                        print "Error:",err
                        con.send('mv_no')
                    os.chdir(os.path.normpath(path+os.sep+os.pardir)) #retrocede uma pasta
                if receive[0]=="rm":
                    print "path: ",path
                    print "atual: ",os.getcwd()
                    cmd = receive[0]+" -rf "+receive[1]
                    print cmd
                    os.chdir(path)

                    op = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                    output, err = op.communicate()
                    if not err:
                        #output=str(op.stdout.read())
                        print "Output:",output
                        con.send('rm_ok')
                    else:
                        print "Error:",err
                        con.send('rm_no')
                    os.chdir(os.path.normpath(path+os.sep+os.pardir)) #retrocede uma pasta

                if receive[0]=="cd":
                    ppath=path
                    print "cd.path: ",path
                    print "atual: ",os.getcwd()
                    if receive[1]=='..': #cd ..
                        path=os.path.normpath(path+os.sep+os.pardir)
                        print "cd.. .path: ",path
                        if os.path.exists(path):
                            #os.chdir("..");
                            print "cd.path2: ",path
                            con.send("cd2ok")
                        else: 
                            con.send("cd2no")
                            path=ppath
                            print "cd.path2: ",path
                    else:

                        path=os.path.join(ppath,receive[1])
                        if os.path.isdir(path):
                            #os.chdir(path)
                            con.send("cd_ok")
                        else:
                            path=ppath
                            con.send("cd_nf")

                if receive[0]=="upload":

                    print "atual: ",os.getcwd()
                    print "receive[1]: ",receive[1]


                    # temp = os.path.relpath(receive[1],os.path.normpath(receive[1]+os.sep+os.pardir))
                    # print "temp: ",temp
                    # temp+='.zip'
                    # print temp

                    with open('temp.zip', 'wb') as fw:
                        msgtam = con.recv(1024) #recebe tam arquivo
                        fsize = int(msgtam)
                        print "fsize: ",fsize
                        rsize = 0
                        con.send("ok") #autoriza enviar
                        while True:
                            data = con.recv(1024)
                            rsize += len(data)
                            fw.write(data)
                            if  rsize >= fsize:
                                break
                    print "Upload Completed"

                    with zipfile.ZipFile('temp.zip',"r") as zip_ref:
                        zip_ref.extractall()

                    os.remove('temp.zip')
                    # sData = con.recv(1024)
                    # print "recebi sData: ",sData
                    # with open(receive[1],"wb") as fDownloadFile:
                    #     print "criei arquivo"
                    #     while sData:
                    #         fDownloadFile.write(sData)
                    #         print "vou receber"
                    #         sData = con.recv(1024)
                    #         print "recebi"
                    # print "Download Completed"

                if receive[0]=="download":

                    print "down.atual: ",os.getcwd()


                    root_dir = os.path.normpath(receive[1]+os.sep+os.pardir)
                    base_dir = os.path.relpath(receive[1],root_dir)

                    try:
                        shutil.make_archive('temp','zip',root_dir,base_dir)

                        fsize = os.path.getsize('temp.zip')
                        print "fsize: ",str(fsize)
                        con.send(str(fsize)) # envia tamanho
                        msg=con.recv(2)
                        if msg=='ok': # se autorizado a receber, envia
                            with open('temp.zip','rb') as fs:
                                data = fs.read(1024)
                                while data:
                                    con.send(data)
                                    data = fs.read(1024)
                            print "Download completed."
                            con.send('down_ok')
                        else: print "Error."

                        os.remove('temp.zip')

                    except OSError:
                        print "File or directory not found."
                        con.send("down_nf")
                        continue

                msg=con.recv(1024)
                receive = decode(msg)
                print "receive3: ",receive
            print "user logout"
            os.chdir(rpath)
            continue

    print 'Ending client connection', cliente
    con.close()
    thread.exit()

tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

orig = (HOST, PORT)

tcp.bind(orig)
tcp.listen(1)

while True:
    con, cliente = tcp.accept()
    thread.start_new_thread(conectado, tuple([con, cliente]))

tcp.close()