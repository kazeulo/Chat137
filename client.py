# client.py
import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

soc = socket.socket()

# function to handle the connection to the server
def connect_to_server():
    server_host = server_ip_entry.get()  # get IP 
    name = name_entry.get()              # get client name 

    if not server_host or not name:
        messagebox.showerror("Error", "Please enter both server IP and your name.")
        return

    try:
        port = 1234
        soc.connect((server_host, port))
        soc.send(name.encode())

        # receive server's response
        soc.recv(1024).decode()

        # close the connection window and start chat
        connection_window.destroy()
        start_chat_window(name, server_host)

    except Exception as e:
        messagebox.showerror("Connection Error", f"Could not connect to the server: {e}")

# function to start the chat window after successful connection
def start_chat_window(name, server_addr):
    global soc

    # create the main chat window
    root = tk.Tk()
    root.title(f"Client Chat - {name}")

    # text area for displaying messages
    chat_area = scrolledtext.ScrolledText(root, width=60, height=20, wrap=tk.WORD)
    chat_area.grid(row=0, column=0, padx=10, pady=10)
    chat_area.config(state=tk.DISABLED)

    # instruction label for entering messages
    instruction_label = tk.Label(root, text="Enter message below:", font=("Arial", 10))
    instruction_label.grid(row=1, column=0, padx=10, pady=0)

    # input field to send messages
    message_entry = tk.Text(root, width=30, height=2, wrap=tk.WORD)
    message_entry.grid(row=2, column=0, padx=10, pady=10)

    # function to update the chat area
    def update_chat_area(message):
        chat_area.config(state=tk.NORMAL)
        chat_area.insert(tk.END, message)
        chat_area.config(state=tk.DISABLED)
        chat_area.yview(tk.END)

    # display the initial message
    update_chat_area(f"Server: {server_addr}. \n\nYou joined the chat!\n\n")

    # function to send messages to the server
    def send_message(event=None):
        message = message_entry.get("1.0", tk.END).strip()  
        if message:
            soc.send(message.encode())
            update_chat_area(f"You: {message}\n")
            message_entry.delete("1.0", tk.END) 

    # bind the Enter key to the send_message function
    root.bind('<Return>', send_message)

    # function to listen for incoming messages from the server and other clients
    def listen_for_messages():
        while True:
            try:
                message = soc.recv(1024).decode()
                if message == "Server has left the chat.":
                    update_chat_area(f"{message}\n")
                    soc.close()
                    root.quit()
                    break
                elif message:
                    update_chat_area(f"{message}\n")
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    # start listening for messages in a separate thread
    threading.Thread(target=listen_for_messages, daemon=True).start()

    # start the chat window GUI loop
    root.mainloop()

# create the connection window for entering server IP and client name
connection_window = tk.Tk()
connection_window.title("Connecting to server...")

# label and entry for server IP
server_ip_label = tk.Label(connection_window, text="Enter Server IP Address:")
server_ip_label.grid(row=0, column=0, padx=10, pady=5)
server_ip_entry = tk.Entry(connection_window, width=30)
server_ip_entry.grid(row=0, column=1, padx=10, pady=5)

# label and entry for client name
name_label = tk.Label(connection_window, text="Enter Your Name:")
name_label.grid(row=1, column=0, padx=10, pady=5)
name_entry = tk.Entry(connection_window, width=30)
name_entry.grid(row=1, column=1, padx=10, pady=5)

# button to initiate connection
connect_button = tk.Button(connection_window, text="Connect", command=connect_to_server)
connect_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

# start the connection window GUI loop
connection_window.mainloop()

# close the socket connection when the program ends
soc.close()
