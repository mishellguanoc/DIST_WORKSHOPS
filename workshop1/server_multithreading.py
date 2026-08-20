from socket import *
import time
from threading import Thread #this is added to admit two or more clients running concurrently

try:
    serverPort = int(input("Enter server port number: "))
except:
    print("Invalid input. Using default port 12000.")
    serverPort = 12000

if serverPort <= 0 or serverPort > 65535:
    serverPort = 12000


serverSocket = socket(AF_INET, SOCK_STREAM)

serverSocket.bind(("", serverPort))

# Permitir varias conexiones pendientes
serverSocket.listen(5)




def handle_client(connectionSocket, addr):
    print(f"[START] Client {addr} connected")

    try:
        message = connectionSocket.recv(1024).decode()

        # El cliente enviará: "Tarea 5"
        parts = message.split()

        task = parts[0]
        seconds = int(parts[1])

        print(f"[TASK] Client {addr}: {task} - {seconds} seconds")

        # Simular una tarea
        for i in range(seconds):
            print(f"[WORK] Client {addr}: {task} - {i + 1}/{seconds}")
            time.sleep(1)

        response = f"{task} completed by server"

        connectionSocket.send(response.encode())

        print(f"[END] Client {addr}: {task} completed")

    except Exception as e:
        print(f"[ERROR] Client {addr}: {e}")

    finally:
        connectionSocket.close()



print(f"Server is ready on port {serverPort}")

while True:
    try:
        connectionSocket, addr = serverSocket.accept()

        clientThread = Thread(
            target=handle_client,
            args=(connectionSocket, addr)
        )

        clientThread.start()

    except KeyboardInterrupt:
        print("\nServer is shutting down.")
        serverSocket.close()
        break