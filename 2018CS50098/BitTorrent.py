from warnings import filterwarnings
import matplotlib.pyplot as plt
import time
from socket import *
import threading
import csv
import sys
import re
filterwarnings("ignore")

start = time.time()
size = 6488666
chunk_size = 10000
chunks = []
f_chunks = []
i=0
while i < (size-chunk_size):
    chunks.append((i,i+chunk_size-1))
    f_chunks.append("")
    i+=chunk_size
chunks.append((i,size-1))
f_chunks.append("")
received = 0
percent = 0
threadLock1 = threading.Lock()
threadLock2 = threading.Lock()
threadLock3 = threading.Lock()

def download(url) :
    flag1=False
    flag2=False
    path = ""
    host = ""
    prev = "a"
    for i in range(len(url)):
        if flag1:
            if url[i]=="/":
                flag1=False
                flag2=True
            else:
                host = host + url[i]
        if flag2:
            if url[i]!=" ":
                path = path + url[i]
        if url[i]=="/" and prev=="/":
            flag1=True
        prev=url[i]
    serverName = host
    serverPort = 80
    x = []
    y = []
    x.append(time.time()-start)
    y.append(0)
    clientSocket = socket(AF_INET,SOCK_STREAM)
    while True:
        try:
            clientSocket.connect((serverName,serverPort))
        except:
            continue
        break
    while True:
        threadLock1.acquire()
        if len(chunks)>0:
            chunk = chunks.pop(0)
            threadLock1.release()
        else:
            threadLock1.release()
            break
        temp1 = "GET "+path+" HTTP/1.1\r\n"
        temp2 = "Host: "+host+"\r\n"
        temp3 = "Accept: text/html\r\n"
        temp4 = "Connection: keep-alive\r\n"
        temp5 = "Range: bytes="+str(chunk[0])+"-"+str(chunk[1])+"\r\n\r\n"
        request = (temp1+temp2+temp3+temp4+temp5).encode('ascii')
        try:
            clientSocket.send(request)
        except:
            threadLock1.acquire()
            chunks.append(chunk)
            threadLock1.release()
            clientSocket.close()
            clientSocket = socket(AF_INET,SOCK_STREAM)
            while True:
                try:
                    clientSocket.connect((serverName,serverPort))
                except:
                    continue
                break
            continue;
        prev = "a"
        response = ""
        flag3=False;
        while True:
            try:
                data = clientSocket.recv(1)
            except:
                threadLock1.acquire()
                chunks.append(chunk)
                threadLock1.release()
                clientSocket.close()
                clientSocket = socket(AF_INET,SOCK_STREAM)
                while True:
                    try:
                        clientSocket.connect((serverName,serverPort))
                    except:
                        continue
                    break
                flag3=True
                break;
            message = data.decode()
            if message == "\r" and prev == "\n":
                try:
                    data = clientSocket.recv(1)
                except:
                    threadLock1.acquire()
                    chunks.append(chunk)
                    threadLock1.release()
                    clientSocket.close()
                    clientSocket = socket(AF_INET,SOCK_STREAM)
                    while True:
                        try:
                            clientSocket.connect((serverName,serverPort))
                        except:
                            continue
                        break
                    flag3=True
                break
            prev = message
            response = response + message
        if flag3:
            continue
        for i in range(chunk[0],chunk[1]+1):
            try:
                data = clientSocket.recv(1)
            except:
                threadLock1.acquire()
                chunks.append((i,chunk[1]))
                threadLock1.release()
                clientSocket.close()
                clientSocket = socket(AF_INET,SOCK_STREAM)
                while True:
                    try:
                        clientSocket.connect((serverName,serverPort))
                    except:
                        continue
                    break
                flag3=True
                break;
            f_chunks[chunk[0]//chunk_size] = f_chunks[chunk[0]//chunk_size] + data.decode()
            x.append(time.time()-start)
            y.append(y[len(y)-1]+1)
            global received
            global percent
            threadLock2.acquire()
            received+=1
            percent = int((received*50)/size)
            sys.stdout.write("\rDownloading: [%s%s] %d%% " % ('#'*percent,' '*(50-percent),int((received*100)/size)))
            threadLock2.release()
        if flag3:
            continue;
        str_list = re.findall("Connection: close", response)
        if len(str_list) > 0:
            clientSocket.close()
            clientSocket = socket(AF_INET,SOCK_STREAM)
            while True:
                try:
                    clientSocket.connect((serverName,serverPort))
                except:
                    continue
                break
    threadLock3.acquire()
    plt.plot(x,y,label=host)
    threadLock3.release()
    clientSocket.close()

plt.title('Download Progress')
plt.xlabel('Time (seconds)')
plt.ylabel('Bytes Downloaded')
threads = []
torrent=open (sys.argv[1],"r")
reader = csv.reader(torrent)
for row in reader:
    for i in range(int(row[1])):
        thread = threading.Thread(target=download,args=(row[0],))
        thread.start()
        threads.append(thread)
for thread in threads:
    thread.join()
sys.stdout.write("\rDownloaded: [%s%s] %d%% \n" % ('#'*percent,' '*(50-percent),2*percent))
plt.legend()
plt.savefig('graph.png')
file = open("big.txt","w")
for i in range(649):
    file.write(f_chunks[i])
file.close()
stop = time.time()
print(f"Download Time = {round(stop-start,4)} seconds")
