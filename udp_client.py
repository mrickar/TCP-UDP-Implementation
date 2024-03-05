import socket
import time
import hashlib
import pickle

def int_to_byte(a:int):
    return a.to_bytes(32,"big")
def byte_to_int(a:bytes):
    return int.from_bytes(a,"big")

def create_packet(seq_num):
    data_header = { 'seq_num': seq_num}
    data_pickle = pickle.dumps(data_header)
    return data_pickle

    
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
            
def Receive_Packet(udp_socket:socket.socket):
    
    received_packets={}
    total_packet = -1
    total_received = 0
    
    #Main loop for receiving packets
    while True:
        if total_received == total_packet: #All packets are recieved no need to continue.
            # print(f"Received all.")
            break   
        try:
            #Waiting packet to receive
            packet_pickle,client_address = udp_socket.recvfrom(bufferSize)
            #Parsing the packet
            packet = pickle.loads(packet_pickle)
            check_sum = packet ["checksum"] #byte type
            seq_num = packet ["seq_num"] #int type
            data = packet ["data"] #byte type
            if LOG: print(f"Received {seq_num}.")
            
        except Exception as e:#if timeout or any corruption, send again
            print(f"Error: {e}")
            continue
        
        
        calculated_checksum = hashlib.md5(data).digest()
        
        #Checksum matches
        if check_sum == calculated_checksum: 
            #Get a packet but total packet size is now known yet. So discard it
            if total_packet == -1 and seq_num != PACKETS_INFO_SEQ: 
                if LOG: print(f"Received {seq_num}. Waiting PACKETS_INFO_SEQ")
                continue
            
            #Get total packet size first time
            if total_packet == -1 and seq_num == PACKETS_INFO_SEQ:
                total_packet = byte_to_int(data) #Initialize total packet count from byte
                received_packets = {str(seq): False for seq in range(0, total_packet)} #Create dictionary for every seq number
                if LOG: print(f"Received PACKETS_INFO_SEQ: total packet = {total_packet}")
                
            #Get a packet and dictionary already created
            elif total_packet != -1 and seq_num != PACKETS_INFO_SEQ :
                if received_packets[str(seq_num)] == False: #Get a sequence number which did not received before.
                    received_packets[str(seq_num)] = data
                    total_received += 1
                    if LOG: print(f"Received {seq_num}")
                    
            #Creating an ACK packet with recieved sequence number.
            #This sequence number could be also be a sequence number which is received before. Client sending ACK again to inform server.
            ack = create_packet(seq_num=seq_num)
            udp_socket.sendto(ack, client_address)
            if LOG: print(f"Sent {seq_num}")
        else:
            if LOG: print(f"Checksum error.")
    
            
    #Sending EOF to server multiple time to decrease the probability of losing EOF packet.
    for i in range(5):
        ack = create_packet(seq_num=EOF_INFO_SEQ)
        udp_socket.sendto(ack, client_address)
        if LOG: print(f"Sent EOF_INFO_SEQ")
    
    #Merging the byte values from dictionary
    return b''.join(list(received_packets.values()))
    
experiment_list=[]
for experiment in range(1,31): 
    print("#################")  
    # You have to set the ip address of the server if you do not use docker compose
    localIP     = "server"
    localPort   = 8000 + experiment
    serverAddressPort   = (localIP, localPort)
    bufferSize          = 2048 
    LOG = False #Should be converted to true for detailed logs.
    relative_path_of_objects = "../objects/" #This is added in front of the md5 file names for path.
    
    #Sequence numbers for first and last packet which are not part of file.
    #These also match in serverside.
    PACKETS_INFO_SEQ = -11
    EOF_INFO_SEQ = -21

    # Create a UDP socket at client side
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    msgFromClient       = "Hello UDP Server" 
    bytesToSend         = str.encode(msgFromClient)
    
    #Setting timeout for sending the hello message
    UDPClientSocket.settimeout(0.5)
    while True:
        try:
            # Send to server using created UDP socket. To send the address of client to the server.
            UDPClientSocket.sendto(bytesToSend, serverAddressPort)
            connected = UDPClientSocket.recv(bufferSize)
            break #if get any message it is success
        except Exception as e:#if timeout, send again
            if LOG: print(f"Error: {e}")
            continue
    
    #Removing timeout
    UDPClientSocket.settimeout(0)
    UDPClientSocket.setblocking(True)
    print(f"Started {experiment}")
    path = ""
    total_start = time.time()
    
    #Receiving all files data
    mega_obj = Receive_Packet(UDPClientSocket)
    print(f"Received all")
    
    #Splitting data for seperate files
    object_list = mega_obj.split(b"EOF_FILE")
    for i in range(10):
        filename = "large-"+str(i)+".obj"
        with open(path+filename, 'wb') as file:
            file.write(object_list[2*i])
        print(f"File written '{filename}'")
        check_total_md5(object_list[2*i],filename)
        print("--------------")
        
        filename = "small-"+str(i)+".obj"
        with open(path+filename, 'wb') as file:
            file.write(object_list[2*i + 1])
        print(f"File written '{filename}'")
        check_total_md5(object_list[2*i+1],filename)
        print("--------------")
    elapsed = time.time() - total_start
    print(f"Experiment {experiment }: Elapsed time {elapsed}")
    experiment_list += [elapsed]
    UDPClientSocket.close()
    print(f"udp_list = {experiment_list}")
    # print(f"Average time elapsed = {elapsed/20}")
    

