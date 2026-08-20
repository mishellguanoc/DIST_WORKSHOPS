from socket import *

serverName = input("Enter server hostname or IP address: ")
if not serverName:
    serverName = "localhost"
try:
    serverPort = int(input("Enter server port number: "))
except:
    print("Invalid input. Using default port 12000.")
    serverPort = 12000

if serverPort <= 0 or serverPort > 65535:
    serverPort = 12000

next = True
while next:
    clientSocket = socket(AF_INET, SOCK_STREAM)
    try:
        clientSocket.connect((serverName, serverPort))
    except Exception as e:
        print("Connection error:", e)
        repeat = input("Do you want to try again? (Y/N)")
        if repeat.upper() == "N":
            break
        else:
            continue
    sentence = input("Input lowercase sentence:")
    clientSocket.send(sentence.encode())
    modifiedSentence = clientSocket.recv(1024)
    print("From Server:", modifiedSentence.decode())
    other = input("Other message: (Y/N)")
    if other.upper() == "N":
        next = False
    clientSocket.close()
