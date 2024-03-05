# echo-server.py

import socket
import os
import pickle
import time

path = "../root/objects/"

def send_file(filename, tcp_socket:socket):
    with open(path+filename, 'rb') as file:
        print(f"Sending file '{filename}'...")
        while True:
            data = file.read(1024)
            if data == b"":
                break
            tcp_socket.sendall(data)
    tcp_socket.sendall("EOF_FILE".encode("utf-8"))
    
    

# Create a TCP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to a specific address and port
server_address = ('0.0.0.0', 12345)
server_socket.bind(server_address)

# Listen for incoming connections
server_socket.listen()

print(f"Server listening on {server_address}")
for experiment in range(1,31): 
    print("#################")
    # Wait for a connectionS
    print("Waiting for a connection...")
    tcp_socket, client_address = server_socket.accept()

    try:
        print(f"Connection from {client_address}")

        for i in range(10):
            large_name = "large-"+str(i)+".obj"
            send_file(large_name,tcp_socket)

            small_name = "small-"+str(i)+".obj"
            send_file(small_name,tcp_socket)
    finally:
    # Clean up the connection
        tcp_socket.close()
server_socket.close()