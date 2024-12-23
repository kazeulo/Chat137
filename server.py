import socket
import threading
import tkinter as tk
from tkinter import scrolledtext
import random

# setup server socket
soc = socket.socket()
host_name = socket.gethostname()
ip = socket.gethostbyname(host_name)
port = 1234
soc.bind((host_name, port))

# list to hold client connections
clients = []

# generator polynomial G(X) = x^4 + x + 1 -> Binary: 10101
generator_polynomial = '10101'

# convert message to binary with 4 zeros appended
def to_binary(message):
    # M(x)
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message_with_zeros = binary_message + '0000'
    return binary_message_with_zeros

# perform binary division using xor
def perform_division(dividend, divisor):
    dividend = list(map(int, dividend))
    divisor = list(map(int, divisor))
    divisor_len = len(divisor)
    
    while len(dividend) >= divisor_len:
        if dividend[0] == 1:  
            for i in range(divisor_len):
                dividend[i] ^= divisor[i]
        dividend.pop(0)
    
    remainder = ''.join(map(str, dividend))
    return remainder

# generate the encoded message
def encoded_message(message, divisor):
    binary_message = to_binary(message)
    remainder = perform_division(binary_message, divisor)
    # T(x)
    encoded_msg = binary_message[:len(binary_message) - 4] + remainder
    return encoded_msg

# introduce 5% error
def add_error(encoded_msg):

    encoded_list = list(encoded_msg)

    if random.random() <= 0.05:
        # get a random index to flip
        index = random.randint(0, len(encoded_list) - 1)

        if encoded_list[index] == '0':
            encoded_list[index] = '1'  
        else:
            encoded_list[index] = '0'  

    return ''.join(encoded_list)

# check CRC 
def check_crc(dividend, divisor):
    remainder = perform_division(dividend, divisor)
    if remainder == '0000':
        return 'Yes'
    else:
        return 'No'

# convert from binary to string
def decode_message(binary_message):
    n = 8

    # for storing decoded message
    decoded_message = "" 

    for i in range(0, len(binary_message), n):
        byte = binary_message[i:i + n]
        
        char_code = int(byte, 2)
        
        # convert integer to correspoding character
        decoded_char = chr(char_code)
        
        # append to decoded message
        decoded_message += decoded_char

    return decoded_message 

# create the GUI window
root = tk.Tk()
root.title("Server")
root.config(bg="lightgray")

frame = tk.Frame(root, padx=20, bg="lightgray")  
frame.pack(fill="both", expand=True, padx=20, pady=10)

title_label = tk.Label(frame, text="Server", font=("Poppins", 14, "bold"), bg="lightgray")
title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=15)

# text area for displaying messages
chat_area = scrolledtext.ScrolledText(frame, width=55, height=15, wrap=tk.WORD)
chat_area.grid(row=1, column=0, padx=10, pady=0)
chat_area.config(state=tk.DISABLED)

# instruction label for entering messages
instruction_label = tk.Label(frame, text="Enter message below.", font=("Poppins", 10), bg="lightgray")
instruction_label.grid(row=2, column=0, padx=10, pady=(10, 0))

# input field for sending message
message_entry = tk.Text(frame, width=30, height=2, wrap=tk.WORD)  
message_entry.grid(row=3, column=0, padx=10, pady=15)

# function to update the chat area in the GUI (Thread-safe)
def update_chat_area(message):
        chat_area.config(state=tk.NORMAL)
        chat_area.insert(tk.END, message)
        chat_area.config(state=tk.DISABLED)
        chat_area.yview(tk.END)

# function for handling messages from clients
def handle_client(connection, addr):
    try:
        client_name = connection.recv(1024).decode()  
        clients.append((connection, client_name))

        broadcast(f"{client_name} has joined the chat!\n", None)
        update_chat_area(f"{client_name} has joined the chat!\n\n")

        while True:
            try:
                message = connection.recv(1024).decode().strip()
                if not message:
                    break  
                
                # broadcast message to the clients
                broadcast(f"{client_name}: {message}\n", connection)

                # perform CRC check and decoding on server-side
                is_valid = check_crc(message, generator_polynomial)

                if is_valid == 'Yes':
                    decoded_message = decode_message(message)
                    update_chat_area(f"{client_name}: {message}\nValid: Yes.\nTranslated Message: {decoded_message}\n\n")
                else:
                    update_chat_area(f"{client_name}: {message}\nValid: No. Message corrupted.\n\n")

            except Exception as e:
                print(f"Error receiving message from {client_name}: {e}")
                break

    except Exception as e:
        print(f"Error with client {client_name}: {e}")

    finally:
        # remove the client and close the connection when done
        clients.remove((connection, client_name))
        connection.close()

        # notify others that the client has left
        broadcast(f"{client_name} has left the chat.\n", None)
        update_chat_area(f"{client_name} has left the chat.\n")

# function for broadcasting message to clients
def broadcast(message, sender_connection):
    for client, _ in clients:
        if client != sender_connection:
            try:
                client.send(message.encode())
            except Exception as e:
                print(f"Error sending message to a client: {e}")
                continue  

# function to accept incoming client connections
def accept_clients():
    soc.listen()
    while True:
        connection, addr = soc.accept()
        threading.Thread(target=handle_client, args=(connection, addr), daemon=True).start()

# function to send a message from the server
def send_message(event=None):
    server_message = message_entry.get("1.0", tk.END).strip() 
    if server_message:
        tx = encoded_message(server_message, generator_polynomial)
        tx_error = add_error(tx)
        broadcast(f"Server: {tx_error}\n\n", None)
        update_chat_area(f"Server: {server_message}\nSent: {tx_error}\n\n")
        message_entry.delete("1.0", tk.END) 

# function to send a shutdown message to all clients and close the server
def shutdown_server():
    shutdown_message = "Server has left the chat."
    broadcast(shutdown_message, None)
    update_chat_area(shutdown_message + "\n")
    
    # close all client connections
    for client, _ in clients:
        client.close()
    
    # close the socket
    soc.close()
    root.quit()

# initial status message
update_chat_area(f"Server is running...\nHost: {ip}\nWaiting for clients to join...\n\n")

# start accepting clients in a separate thread
threading.Thread(target=accept_clients, daemon=True).start()

# bind the Enter key to the send_message function
root.bind('<Return>', send_message)

def on_closing():
    shutdown_server()

root.protocol("WM_DELETE_WINDOW", on_closing)

# start the GUI loop
root.mainloop()