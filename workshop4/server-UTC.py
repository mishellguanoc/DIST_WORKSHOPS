import zmq
import time

port = "5000"
def utc_time_server():
    context = zmq.Context()
    socket = context.socket(zmq.REP)  	# REP stands for Reply
    socket.bind("tcp://*:" + port)  	# Bind to port 5000

    print("UTC Time Server running...")

    while True:
        # Wait for next request from client
        message = socket.recv()
        print(f"Received request: {message.decode()}")

        # Get UTC time
        utc_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())

        # Send UTC time back to client
        socket.send_string(utc_time)
        print(f"Sent UTC time: {utc_time}")

if __name__ == "__main__":
    utc_time_server()

