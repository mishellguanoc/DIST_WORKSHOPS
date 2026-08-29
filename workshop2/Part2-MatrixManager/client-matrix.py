"""
Distributed Matrix Manager - Client (RMI / XML-RPC)
Part 2 of Workshop 2 - Distributed Systems

The client reads (or randomly generates) two matrices and asks the user
which operation to perform (add, sub, prod). It sends the request to the
remote server through XML-RPC and prints the resulting matrix.
"""

import xmlrpc.client
import numpy as np


def read_matrix(name):
    """
    Lets the user choose between manually typing a matrix or generating
    a random one, and returns it as a nested list (what XML-RPC can send).
    """
    mode = input(f"Matrix {name}: (m)anual or (r)andom? [r]: ").strip().lower()

    if mode == "m":
        rows = int(input(f"  Number of rows for {name}: "))
        cols = int(input(f"  Number of columns for {name}: "))
        matrix = []
        for i in range(rows):
            row_str = input(f"  Row {i} (values separated by spaces): ")
            row = [float(x) for x in row_str.split()]
            if len(row) != cols:
                raise ValueError("The row does not have the expected number of columns")
            matrix.append(row)
        return matrix
    else:
        rows = int(input(f"  Number of rows for {name} [3]: ") or 3)
        cols = int(input(f"  Number of columns for {name} [3]: ") or 3)
        matrix = np.random.randint(1, 10, size=(rows, cols)).tolist()
        print(f"  Generated {name} =\n{np.array(matrix)}")
        return matrix


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

    proxy = xmlrpc.client.ServerProxy(f"http://{serverName}:{serverPort}/RPC2")

    op = ""
    while op not in ("add", "sub", "prod"):
        op = input("Operation to perform (add / sub / prod): ").strip().lower()

    print("\n-- Matrix A --")
    matA = read_matrix("A")
    print("\n-- Matrix B --")
    matB = read_matrix("B")

    try:
        result = proxy.compute(op, matA, matB)
        print(f"\nResult of '{op}':")
        print(np.array(result))
    except xmlrpc.client.Fault as e:
        print(f"Remote error: {e.faultString}")


if __name__ == "__main__":
    main()
