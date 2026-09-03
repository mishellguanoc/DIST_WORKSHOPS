import uuid
import socket

entity_id = uuid.uuid5(uuid.NAMESPACE_DNS, "ismael")

hostname = socket.gethostname()
ip = socket.gethostbyname(hostname)

entity = {
        "id": str(entity_id),
        "address": (ip, 6000)
        }

print("\n", entity)