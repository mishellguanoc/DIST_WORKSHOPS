from socket import *
import time

try:
    serverPort = int(input("Enter server port number: "))
except:
    print("Invalid input. Using default port 12000.")
    serverPort = 12000

if serverPort <= 0 or serverPort > 65535:
    serverPort = 12000

serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(("", serverPort))
serverSocket.listen(1)
print("The server is ready to receive")

while True:
    try:
        connectionSocket, addr = serverSocket.accept()
    except KeyboardInterrupt:
        print("\nServer is shutting down.")
        break
    print("From Client:", addr)

    # Loop mientras la misma conexión siga enviando mensajes
    while True:
        try:
            data = connectionSocket.recv(1024)
        except Exception as e:
            print("Error receiving data:", e)
            break

        if not data:
            # El cliente cerró la conexión (recv devuelve b'' cuando se acaba)
            print("Client closed the connection.")
            break

        sentence = data.decode()
        print("I received:", sentence)
        capitalizedSentence = sentence.upper()
        time.sleep(3)

        try:
            connectionSocket.send(capitalizedSentence.encode())
        except Exception as e:
            print("Error sending data:", e)
            break

    try:
        connectionSocket.close()
    except Exception as e:
        print("Error closing connection:", e)