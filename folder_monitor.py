# folder_monitor.py 

import time
import socket
import json
import os  
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess 
import threading
from Crypto.PublicKey import RSA
import base64

class Watcher:
    DIRECTORY_TO_WATCH = "DesignatedFolder"  

    def __init__(self, server_address):
        self.observer = Observer()
        self.server_address = server_address
        self.client_socket = None
        self.key_pair = RSA.generate(2048)  # Generate new RSA keys
        self.public_key = self.key_pair.publickey().exportKey() 
        self.private_key = self.key_pair.exportKey()    
        self.private_key_encoded = base64.urlsafe_b64encode(self.private_key).decode('utf-8')

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.server_address)
        # Send an initial message to identify this client as a 'seeder'
        self.client_socket.sendall(b'seeder')  # Sending 'seeder' as bytes
        time.sleep(0.5)  # Wait for half a second

    def run(self):
        print("Starting the watcher...")
        self.connect_to_server()  # Establish connection to the server

        # Start listening for instructions in a new thread after connection is established
        instructions_thread = threading.Thread(target=self.listen_for_instructions)
        instructions_thread.start()

        event_handler = Handler(self.client_socket, self.public_key)
        self.send_initial_files(event_handler)
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")
            self.client_socket.close()  # Close the connection when done

        self.observer.join()
    
    def send_initial_files(self, handler):
        for root, dirs, files in os.walk(self.DIRECTORY_TO_WATCH):
            for filename in files:
                filepath = os.path.join(root, filename)
                handler.send_message('ADD', filepath)
                time.sleep(0.1)  # Add a short delay between sends

    def handle_transfer_instruction(self, session_id, file_path, leecher_public_key_encoded):
        # Start the new process
        print(f"Starting a new process for {file_path} with session ID {session_id}...")
        subprocess.Popen(['start', 'cmd', '/k', 'python', 'secure_seeder.py', str(session_id), str(file_path), self.private_key_encoded, leecher_public_key_encoded], shell=True)
    
    def listen_for_instructions(self):
        print("Listening for instructions from the server...")
        try:
            while True:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    break  # No more data from the server

                message = json.loads(data)
                if message['type'] == 'TRANSFER':
                    print("Received transfer instruction from the server.")
                    # Extract the session information
                    session_info = message['session']
                    session_id = session_info['session_id']
                    file_path = session_info['file_path']  
                    leecher_public_key = session_info['public_key'] 
                    leecher_public_key_encoded = base64.urlsafe_b64encode(leecher_public_key.encode('utf-8')).decode('utf-8')

                    # Pass the session ID and file path to the method that handles the transfer
                    self.handle_transfer_instruction(session_id, file_path, leecher_public_key_encoded)
        except Exception as e:
            print(f"Error while listening for instructions: {e}")
        finally:
            self.client_socket.close()

class Handler(FileSystemEventHandler):
    def __init__(self, client_socket, public_key):
        self.client_socket = client_socket
        self.public_key = public_key    
        self.public_key_decoded = public_key.decode('utf-8')    
        # print(f"Public key decoded: {self.public_key_decoded}") # remove later <--------

    def send_message(self, action, filepath):
        # Extract filename and size from filepath
        filename = os.path.basename(filepath)
        if action == 'ADD':
            filesize = os.path.getsize(filepath)  # Get the size of the file
        else:
            filesize = 0
        # Constructing and sending JSON formatted message
        message = json.dumps({
            'type': action,
            'filename': filename,
            'filelocation': filepath,
            'filesize': filesize,  # Add the file size here
            'public_key': self.public_key_decoded

        }) + '\n'
        self.client_socket.sendall(message.encode('utf-8'))

    def on_created(self, event):
        if not event.is_directory:
            self.send_message('ADD', event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.send_message('DELETE', event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            # Send DELETE for old location and ADD for new location
            self.send_message('DELETE', event.src_path)
            self.send_message('ADD', event.dest_path)

if __name__ == '__main__':
    # localhost: '127.0.0.1'
    SERVER_HOST = '35.224.31.170'     # Server's IP address
    SERVER_PORT = 65420               # Server's port
    w = Watcher((SERVER_HOST, SERVER_PORT))
    w.run()

