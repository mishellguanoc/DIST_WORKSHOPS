# This code send a certain amount of messages
# to the server and then terminate the communication

from socket import *
import random
import string

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

# Generate a random number of messages to send (between 1 and 10 messages)
numMessages = random.randint(1, 10)
print(f"{numMessages} messages would be sent to the server")

def generateRandomMessage():
    length = random.randint(5, 15)
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for _ in range(length))

clientSocket = socket(AF_INET, SOCK_STREAM)
try:
    clientSocket.connect((serverName, serverPort))
except Exception as e:
    print("Connection error:", e)
    exit()

for i in range(numMessages):
    sentence = generateRandomMessage()
    print(f"Mensaje {i+1}: {sentence}")
    clientSocket.send(sentence.encode())
    modifiedSentence = clientSocket.recv(1024)
    print("From Server:", modifiedSentence.decode())

clientSocket.close()
print("Comunicación terminada.")