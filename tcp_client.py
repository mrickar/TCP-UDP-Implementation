import socket
import pickle
import hashlib
import time

relative_path_of_objects = "../objects/" #This is added in front of the md5 file names for path.
def check_total_md5(received_data:bytes,filename:str):
    calculated_md5=hashlib.md5(received_data).hexdigest()
    try:
        with open(relative_path_of_objects+filename+".md5", 'r') as file:  
            md5 = file.readline()[:-1]  
            if calculated_md5 == md5:
                print("Checksum Matched")
            else:
                print("Checksum Not Matched")
    except:
        print(f"Could not find {relative_path_of_objects+filename}.md5 to check.")

experiment_list=[]
for experiment in range(1,31): 
    print("#################")
    print(f"Started {experiment}")
    # Create a TCP/IP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_ip=socket.gethostbyname("server")
    # Connect to the server's address and port
    server_address = (server_ip, 12345)
    client_socket.connect(server_address)
    path = ""

    total_start = time.time()
    mega_obj = b""
    
    #Receiving packets untill there is no data left
    while True:
        data = client_socket.recv(65000)
        if data == b"":
            break
        mega_obj += data
    print(f"Received all")
    
    #Splitting files to seperate
    object_list = mega_obj.split(b"EOF_FILE")
    for i in range(10):
        filename = "large-"+str(i)+".obj"
        with open(path+filename, 'wb') as file:
            file.write(object_list[2*i])
        print(f"File written '{filename}'")
        # check_total_md5(object_list[2*i],filename)
        print("--------------")
        
        filename = "small-"+str(i)+".obj"
        with open(path+filename, 'wb') as file:
            file.write(object_list[2*i + 1])
        print(f"File written '{filename}'")
        # check_total_md5(object_list[2*i+1],filename)
        print("--------------")
    elapsed = time.time() - total_start
    print(f"Experiment {experiment}: Elapsed time {elapsed}")
    experiment_list.append(elapsed)
    print(f"tcp_list = {experiment_list}")
    # print(f"Average time elapsed = {elapsed/20}")


    # Clean up the connection
    client_socket.close()

