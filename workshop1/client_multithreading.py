from socket import *
from threading import Thread
import time

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


def client_task(client_id, task_name, duration):
    clientSocket = socket(AF_INET, SOCK_STREAM)

    try:
        clientSocket.connect((serverName, serverPort))

        print(f"[CLIENT {client_id}] Connected to server")
        print(f"[CLIENT {client_id}] Sending: {task_name} {duration}")

        message = f"{task_name} {duration}"

        clientSocket.send(message.encode())

        modifiedSentence = clientSocket.recv(1024).decode()

        print(f"[CLIENT {client_id}] Server response: {modifiedSentence}")

    except Exception as e:
        print(f"[CLIENT {client_id}] Connection error: {e}")

    finally:
        clientSocket.close()
        print(f"[CLIENT {client_id}] Connection closed")


# Número de clientes que queremos crear
number_of_clients = 3

# Crear los clientes
clients = []

for i in range(number_of_clients):

    client_id = i + 1
    task_name = f"Task{client_id}"
    duration = (client_id * 2) + 1

    clientThread = Thread(
        target=client_task,
        args=(client_id, task_name, duration)
    )

    clients.append(clientThread)
    clientThread.start()


# Esperar a que todos los clientes terminen
for clientThread in clients:
    clientThread.join()

print("\nAll clients have finished.")