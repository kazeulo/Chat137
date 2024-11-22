# server.py
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext

# setup server socket
soc = socket.socket()
host_name = socket.gethostname()
ip = socket.gethostbyname(host_name)
port = 1234
soc.bind((host_name, port))

# list to hold client connections
clients = []

# create the GUI window
root = tk.Tk()
root.title("Server")

# text area for displaying messages
chat_area = scrolledtext.ScrolledText(root, width=60, height=20, wrap=tk.WORD)
chat_area.grid(row=0, column=0, padx=10, pady=10)
chat_area.config(state=tk.DISABLED)

# instuction for entering message
instruction_label = tk.Label(root, text="Enter message below:", font=("Arial", 10))
instruction_label.grid(row=1, column=0, padx=10, pady=0)

# input field for sending message
message_entry = tk.Text(root, width=30, height=2, wrap=tk.WORD)  
message_entry.grid(row=2, column=0, padx=10, pady=15)

# function to update the chat area in the GUI
def update_chat_area(message):
    chat_area.config(state=tk.NORMAL)
    chat_area.insert(tk.END, message)
    chat_area.config(state=tk.DISABLED)
    chat_area.yview(tk.END)

# function to handle individual client communication
def handle_client(connection, addr):
    client_name = connection.recv(1024).decode()
    clients.append((connection, client_name))

    # broadcast the "has joined" message
    broadcast(f"{client_name} has joined the chat!", None)
    update_chat_area(f"{client_name} has joined the chat!\n")

    while True:
        try:
            message = connection.recv(1024).decode()
            if message:
                broadcast(f"{client_name}: {message}", connection)
                update_chat_area(f"{client_name}: {message}\n")
            else:
                break
        except:
            break

    clients.remove((connection, client_name))
    connection.close()

    # notify others that the client has left
    broadcast(f"{client_name} has left the chat.", None)
    update_chat_area(f"{client_name} has left the chat.\n")

# function to broadcast messages to all clients
def broadcast(message, sender_connection):
    for client, _ in clients:
        if client != sender_connection:
            try:
                client.send(message.encode())
            except:
                continue

# function to accept incoming client connections
def accept_clients():
    # wait for incoming connections
    soc.listen()
    while True:
        connection, addr = soc.accept()
        threading.Thread(target=handle_client, args=(connection, addr), daemon=True).start()

# function to send a message from the server
def send_message(event=None):
    server_message = message_entry.get("1.0", tk.END).strip() 
    if server_message:
        broadcast(f"Server: {server_message}", None)
        update_chat_area(f"Server: {server_message}\n")
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

# atart the GUI loop
root.mainloop()
