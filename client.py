import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
import random

# Generator polynomial G(X) = x^4 + x + 1 -> Binary: 10101
generator_polynomial = '10101'

# Functions for CRC encoding and decoding (same as your current code)

# AS SENDER

# convert string into binary
# append 4 zeros
def to_binary(message):
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message_with_zeros = binary_message + '0000'
    return binary_message_with_zeros

# perform binary division with xor
def division(dividend, divisor):
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

# get final encoded message
def encoded_message(message, divisor):
    binary_message = to_binary(message)
    remainder = division(binary_message, divisor)
    encoded_msg = binary_message[:len(binary_message) - 4] + remainder 
    return encoded_msg

# introduce 5% error
def add_error(encoded_msg):
    encoded_list = list(encoded_msg)
    if random.random() < 0.05:  
        error_index = random.randint(0, len(encoded_list) - 1)
        encoded_list[error_index] = '1' if encoded_list[error_index] == '0' else '0'
    return ''.join(encoded_list)

# AS RECEIVER
# check if message is valid by performing binary division
def check_crc(dividend, divisor):
    dividend = list(map(int, dividend))
    divisor = list(map(int, divisor))
    divisor_len = len(divisor)
    
    while len(dividend) >= divisor_len:
        if dividend[0] == 1:
            for i in range(divisor_len):
                dividend[i] ^= divisor[i]
        dividend.pop(0)
    
    remainder = ''.join(map(str, dividend))
    if remainder == '0000':
        return 'Yes'
    else:
        return 'No'

# convert from binary to string
def decode_message(binary_message):
    n = 8  # 8-bit chars
    decoded_chars = [chr(int(binary_message[i:i + n], 2)) for i in range(0, len(binary_message), n)]
    return ''.join(decoded_chars)

# client socket handling
def connect_to_server():
    server_host = server_ip_entry.get()  # Get the server IP
    name = name_entry.get()              # Get client name

    if not server_host or not name:
        messagebox.showerror("Error", "Please enter both server IP and your name.")
        return

    try:
        port = 1234
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((server_host, port))
        client_socket.send(name.encode())  # Send the client name

        # receive server's response
        client_socket.recv(1024).decode()

        # close the connection window and start the chat window
        connection_window.destroy()
        start_chat_window(name, server_host, client_socket)

    except Exception as e:
        messagebox.showerror("Connection Error", f"Could not connect to the server: {e}")

def start_chat_window(name, server_addr, client_socket):
    root = tk.Tk()
    root.title(f"Client Chat - {name}")
    root.config(bg="lightgray")

    frame = tk.Frame(root, padx=20, bg="lightgray")  
    frame.pack(fill="both", expand=True, padx=20, pady=10)

    # server label
    title_label = tk.Label(frame, text="Client", font=("Poppins", 14, "bold"), bg="lightgray")
    title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=15)

    # text area for displaying messages
    chat_area = scrolledtext.ScrolledText(frame, width=70, height=15, wrap=tk.WORD)
    chat_area.grid(row=1, column=0, padx=10, pady=0)
    chat_area.config(state=tk.DISABLED)

    # instruction label for entering messages
    instruction_label = tk.Label(frame, text="Enter message below.", font=("Poppins", 10), bg="lightgray")
    instruction_label.grid(row=2, column=0, padx=10, pady=(10, 0))

    # input field to send messages
    message_entry = tk.Text(frame, width=30, height=2, wrap=tk.WORD)
    message_entry.grid(row=3, column=0, padx=10, pady=15)

    def update_chat_area(message):
        chat_area.config(state=tk.NORMAL)
        chat_area.insert(tk.END, message)
        chat_area.config(state=tk.DISABLED)
        chat_area.yview(tk.END)

    update_chat_area(f"Server: {server_addr}. \n\nYou joined the chat!\n\n")

    # function to send messages to the server
    def send_message(event=None):
        message = message_entry.get("1.0", tk.END).strip()
        if message:
            crc_message = encoded_message(message, generator_polynomial)    # encode message
            crc_message_error = add_error(crc_message)                      # introduce 5% error
            client_socket.send(crc_message_error.encode())
            update_chat_area(f"You: {message}\nSent: {crc_message_error}\n\n")
            message_entry.delete("1.0", tk.END)

    root.bind('<Return>', send_message)

    def listen_for_messages():
        while True:
            try:
                message = client_socket.recv(1024).decode().strip()

                if message == "Server has left the chat.":
                    update_chat_area(f"{message}\n")
                    client_socket.close()
                    root.quit()  # Exit the client GUI
                    break

                if message:
                    if "has joined the chat!" in message or "has left the chat." in message:
                        # handle join/leave notifications without CRC or decoding
                        update_chat_area(f"{message}\n")
                    else:
                        sender, message_content = message.split(":", 1)
                        sender = sender.strip()
                        message_content = message_content.strip()

                        # Perform CRC check to validate the message
                        is_valid = check_crc(message_content, generator_polynomial)
                        if is_valid == 'Yes':
                            # Decode the valid message
                            decoded_message = decode_message(message_content)
                            update_chat_area(f"{sender}: {message_content}\nValid: Yes.\nDecoded Message: {decoded_message}\n\n")
                        else:
                            update_chat_area(f"{sender}: {message_content}\nValid: No.\n\n")

            except Exception as e:
                print(f"Error receiving message: {e}")
                break

    # start listening for messages in a separate thread
    threading.Thread(target=listen_for_messages, daemon=True).start()

    # start the GUI loop
    root.mainloop()

# create the connection window for entering server IP and client name
connection_window = tk.Tk()
connection_window.title("Connecting to server...")

server_ip_label = tk.Label(connection_window, text="Enter Server IP Address:")
server_ip_label.grid(row=0, column=0, padx=10, pady=5)
server_ip_entry = tk.Entry(connection_window, width=30)
server_ip_entry.grid(row=0, column=1, padx=10, pady=5)

name_label = tk.Label(connection_window, text="Enter Your Name:")
name_label.grid(row=1, column=0, padx=10, pady=5)
name_entry = tk.Entry(connection_window, width=30)
name_entry.grid(row=1, column=1, padx=10, pady=5)

connect_button = tk.Button(connection_window, text="Connect", command=connect_to_server)
connect_button.grid(row=2, column=0, columnspan=2, padx=10, pady=10)

connection_window.mainloop()
