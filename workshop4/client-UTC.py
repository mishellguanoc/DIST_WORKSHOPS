import zmq
import threading
import time

hostname = "localhost"
port = "5000"
def utc_time_client():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)  # REQ stands for Request
    socket.connect("tcp://" + hostname + ":" + port)  # Connect to the server's port

    # Send a request for UTC time
    socket.send_string("Time request")

    # Receive the UTC time from the server
    utc_time = socket.recv().decode('utf-8')
    print(f"Received UTC time: {utc_time}")

if __name__ == "__main__":
    c = [ ]
    for ii in range(3):
        c.append(threading.Thread(target=utc_time_client(), args=()))
        c[ii].start()
        time.sleep(2)
        c[ii].join()
    print('Done')

