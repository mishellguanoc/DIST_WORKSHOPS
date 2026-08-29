"""
Distributed Matrix Manager - Server (RMI / XML-RPC)
Part 2 of Workshop 2 - Distributed Systems

The server exposes a single remote method, `compute`, that receives two
matrices (as nested lists, since XML-RPC cannot transport numpy arrays
directly) and an operation name ("add", "sub" or "prod"). It converts the
lists back into numpy arrays, performs the operation and returns the result
as a nested list again.
"""

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import numpy as np


# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


def compute(op, matA, matB):
    """
    Remote method: performs add / sub / prod (matrix product) on two
    matrices sent by the client.

    matA, matB: nested lists (rows of numbers)
    op: "add", "sub" or "prod"
    returns: nested list with the result, or an XML-RPC Fault on error
    """
    A = np.array(matA, dtype=float)
    B = np.array(matB, dtype=float)

    print(f"[SERVER] Received op='{op}'")
    print(f"[SERVER] A =\n{A}")
    print(f"[SERVER] B =\n{B}")

    if op == "add":
        if A.shape != B.shape:
            raise ValueError(f"Shape mismatch for add: {A.shape} vs {B.shape}")
        result = A + B
    elif op == "sub":
        if A.shape != B.shape:
            raise ValueError(f"Shape mismatch for sub: {A.shape} vs {B.shape}")
        result = A - B
    elif op == "prod":
        if A.shape[1] != B.shape[0]:
            raise ValueError(
                f"Shape mismatch for prod: {A.shape} x {B.shape} (cols(A) must equal rows(B))"
            )
        result = A @ B
    else:
        raise ValueError(f"Unknown operation: {op}")

    print(f"[SERVER] Result =\n{result}")
    return result.tolist()


def main():
    serverName = input("Enter server hostname or IP address: ")
    if not serverName:
        serverName = "localhost"
    try:
        serverPort = int(input("Enter server port number: "))
    except ValueError:
        print("Invalid input. Using default port 12000.")
        serverPort = 12000

    if serverPort <= 0 or serverPort > 65535:
        serverPort = 12000

    # Create server. allow_none lets numpy/None values pass through cleanly.
    with SimpleXMLRPCServer((serverName, serverPort),
                             requestHandler=RequestHandler,
                             allow_none=True) as server:
        server.register_introspection_functions()
        server.register_function(compute, 'compute')

        print(f"Matrix Manager server listening on {serverName}:{serverPort}...")
        server.serve_forever()


if __name__ == "__main__":
    main()
