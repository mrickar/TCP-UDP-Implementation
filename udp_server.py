import socket
import hashlib
import pickle
import time
import sys
def int_to_byte(a:int):
    return a.to_bytes(32,"big")
def byte_to_int(a:bytes):
    return int.from_bytes(a,"big")
    
    
def create_packet(check_sum,seq_num,data):
    data_header = { 'checksum': check_sum, 'seq_num': seq_num, "data":data}
    data_pickle = pickle.dumps(data_header)
    return data_pickle

def Send_Packet(all_obj,udp_socket:socket.socket,address):        
    
    full_data =[]
    total_packet=0
    
    #Reading whole file and storing the packets in an array
    for data in all_obj:
        check_sum = hashlib.md5(data).digest() #Checksum of the current packet
        packet = create_packet(check_sum=check_sum,seq_num=total_packet,data=data)
        full_data.append(packet)
        total_packet+=1

    is_received_EOF = False
    #Loop for sending total packet count
    while True:
        try:
            #Calculating check sum of total packet count
            check_sum = hashlib.md5(int_to_byte(total_packet)).digest()
            #A packet with data is total packet count and sequence number with PACKETS_INFO_SEQ constant
            packet_info = create_packet(check_sum=check_sum,seq_num=PACKETS_INFO_SEQ,data=int_to_byte(total_packet))
            udp_socket.sendto(packet_info,address)
            if LOG: print(f"Send PACKETS_INFO_SEQ")
            #Waiting for ACK response
            ack_response_pickle, _ = udp_socket.recvfrom(bufferSize)
            ack_response = pickle.loads(ack_response_pickle)
            rec_seq_num = ack_response ["seq_num"]
            if LOG: print(f"Received: {ack_response}")
            #If response is from same file and sequence number is as wanted, start sending file
            if rec_seq_num == PACKETS_INFO_SEQ:
                break
        except Exception as e:#if timeout, send again
            if LOG: print(f"Error: {e}")
            continue
    
    #Storing received sequence numbers in responses
    received_ack = {str(seq): False for seq in range(0, total_packet)}
    
    acked_count=0
    last_checked=0

    #Until receiving EOF response
    while is_received_EOF == False:
        
        #Sending N packets each time
        sent_count=0 #Tracking the sent packet number each loop
        while sent_count != N:
            #If ACK of packet with sequence number i is not received, send it
            if received_ack[str(last_checked)] == False:
                udp_socket.sendto(full_data[last_checked],address)
                sent_count += 1
                if LOG: print(f"Sent packet with seq {last_checked}")
            last_checked += 1
            last_checked %= total_packet
        
        
        #Wait for N ACK
        for i in range(N):
            try:    
                #Parsing response
                ack_response_pickle, _ = udp_socket.recvfrom(bufferSize)
                ack_response = pickle.loads(ack_response_pickle)
                rec_seq_num = ack_response ["seq_num"]
                if LOG: print(f"Received {ack_response}")
                
                #From previous file or Response of packet count, discard it
                if rec_seq_num == PACKETS_INFO_SEQ:
                    if LOG: print(f"Received from wrong file or PACKETS_INFO_SEQ")
                    continue
                
                #Client informing received all packets, finish sending
                if rec_seq_num == EOF_INFO_SEQ :
                    is_received_EOF = True
                    if LOG: print(f"Received EOF")
                    break
                
                #Received ACK with sequnce number in response first time, mark it
                if received_ack[str(rec_seq_num)] == False:
                    received_ack[str(rec_seq_num)] = True
                    acked_count +=1
                    print(f"%{(acked_count)/total_packet*100} acked.")
                    if acked_count == total_packet:
                        is_received_EOF = True
                        break
            except Exception as e:#if timeout, send again
                if LOG: print(f"Error: {e}")
                break
    
    
for experiment in range(1,31): 
    print("#################")  
    print(f"Experiment {experiment}:")           
    # You have to set your own ip address of eth0 if you do not use docker compose
    localIP     = "server"
    localPort   = 8000 + experiment
    bufferSize  = 1024
    serverAddressPort   = (localIP, localPort)
    relative_path_of_objects = "../root/objects/" #This is added in front of the object names for path.
    N = 42 #Window size
    timeout_seconds = 0.005 #timeout
    LOG = False #Should be converted to true for detailed logs.

    #Sequence numbers for first and last packet which are not part of file.
    #These also match in client side.
    PACKETS_INFO_SEQ = -11
    EOF_INFO_SEQ = -21       

    # Create a datagram socket
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    # Bind to address and ip
    UDPServerSocket.bind(serverAddressPort)

    print("UDP server up and listening")
    message,address = UDPServerSocket.recvfrom(bufferSize)
    print(address)
    clientMsg = "{}".format(message)
    bytesToSend = str.encode(clientMsg)
    clientIP  = "Client IP Address:{}".format(address)
    print(clientMsg)
    # Set a timeout for socket operations (in seconds)
    UDPServerSocket.settimeout(timeout_seconds)
    # Listen for incoming datagrams


    full_data = []
    for i in range(10):
        large_name = "large-"+str(i)+".obj"
        with open(relative_path_of_objects+large_name, 'rb') as file:
            while True:
                data = file.read(bufferSize)
                if data == b"": #Read the all file
                    break
                full_data.append(data)
            full_data.append("EOF_FILE".encode("utf-8"))
        small_name = "small-"+str(i)+".obj"
        with open(relative_path_of_objects+small_name, 'rb') as file:
            while True:
                data = file.read(bufferSize)
                if data == b"": #Read the all file
                    break
                full_data.append(data)
            full_data.append("EOF_FILE".encode("utf-8"))
    Send_Packet(full_data,UDPServerSocket,address)  
    UDPServerSocket.close()
    
    

    