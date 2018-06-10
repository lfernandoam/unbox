import socket
import thread

HOST = ''              # Endereco IP do Servidor
PORT = 5000            # Porta que o Servidor esta

users = {}

def decode(msg):
    (mode,username,pwd) = msg.split()
    return mode,username,pwd

def signup(user,pwd): #def signup(users):

    with open("bd.txt","a") as f:
        f.write(user+" "+pwd+"\n")
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
            (username, pwd) = line.split()
            users[username] = pwd
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
    return -1


def conectado(con, cliente):
    print 'A connection was successfully established with', cliente

    while True:
        #print "oi"
        msg = con.recv(1024)
        if not msg: break
        if msg=="fin": break
        print cliente, msg
        receive = decode(msg)
        # print "<DEBUG> mode: ",mode
        # print "<DEBUG> username: ",user,", pwd: ",pwd
        if receive[0]=="1":
            mode,user,pwd = decode(msg)
            signup(user,pwd)
        elif receive[0]=="2":
            mode,user,pwd = decode(msg)
            if(signin(con,user)==-1):
                con.send("user_nf") #user not found

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