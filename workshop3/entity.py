# ip adrre 172.23.204.164


import socket

ENTITY_ID = "ismael"
PORT = 60000

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", PORT))

print("Entity waiting for location requests...")

while True:
    data, addr = sock.recvfrom(1024)
    message = data.decode()
    if message == ENTITY_ID:
        response = f"{ENTITY_ID}:{socket.gethostbyname(socket.gethostname())}"
        sock.sendto(response.encode(), addr)