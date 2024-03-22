# folder_monitor.py / folder_monitor_gui.py
 
import sys  
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
    def __init__(self, server_address, directory_to_watch):
        self.observer = Observer()                    # Create an observer object using the watchdog library          
        self.directory_to_watch = directory_to_watch  # Store the directory to watch, the destination folder
        self.server_address = server_address         
        self.client_socket = None    
        
        # Note: Generate RSA keys pair, this was done in the hopes of implementing a signature verification, 
        # But was not implemented, but can be implemented in the future if needed.
        # Thus even though these keys are being passed around, they are not being used for anything YET.
        self.key_pair = RSA.generate(2048)            
        self.public_key = self.key_pair.publickey().exportKey() 
        self.private_key = self.key_pair.exportKey()    
        self.private_key_encoded = base64.urlsafe_b64encode(self.private_key).decode('utf-8')

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.server_address)
        # Send an initial message to identify this client as a 'seeder'
        self.client_socket.sendall(b'seeder')  
        time.sleep(0.5)  # Wait for half a second to avoid message collision/overlap

    def run(self):
        print("Starting the watcher...")
        self.connect_to_server()  # Establish connection to the server

        # Start listening for instructions in a new thread after connection is established
        instructions_thread = threading.Thread(target=self.listen_for_instructions)
        instructions_thread.start()

        # create a function handler object to handle the events
        event_handler = Handler(self.client_socket, self.public_key)

        # Send the initial files in the directory to the server as soon as it connects to the lookup server
        self.send_initial_files(event_handler)

        # Schedule the observer to watch the directory, this is watchdog library specifics
        self.observer.schedule(event_handler, self.directory_to_watch, recursive=True)  # recursive=True means it will watch subdirectories
        self.observer.start()  # A separate thread is created to watch the directory, done by watchdog library

        try:
            # The main thread is kept looping indefinitely, to keep the observer and listening to the server running
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.observer.stop()
            print("Observer Stopped")
            self.client_socket.close()  

        # self.observer.join() 
    
    def send_initial_files(self, handler):
        for root, dirs, files in os.walk(self.directory_to_watch):
            for filename in files:
                filepath = os.path.join(root, filename)
                handler.send_message('ADD', filepath)
                time.sleep(0.1)  # Add a short delay between sends, to avoid message collision/overlap
    

    def handle_transfer_instruction(self, session_id, file_path, leecher_public_key_encoded):
        # Start the new indipedent process with its own terminal 
        print(f"Starting a new process for {file_path} with session ID {session_id}...")
    # For Windows
        # old code
        # subprocess.Popen(['start', 'cmd', '/k', 'python', 'seeder.py', str(session_id), str(file_path), self.private_key_encoded, leecher_public_key_encoded], shell=True)
        # new code
        subprocess.Popen(['start', 'cmd', '/k', 'python', 'seeder.py', str(session_id), str(file_path), self.private_key_encoded, leecher_public_key_encoded], shell=True)
        # exe code
        # subprocess.Popen(['start', 'cmd', '/k', 'seeder.exe', str(session_id), str(file_path), self.private_key_encoded, leecher_public_key_encoded], shell=True)

    def listen_for_instructions(self):
        print("Listening for instructions from the server...")
        try:
            # Listen for instructions from the server indefinitely
            while True:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    break  # No more data from the server, break out of the loop

                message = json.loads(data)
                # This message is sent by the lookup server, when someone wants to request a file from the file host
                # This is an command instructing the folder_monitor to start a new seeder process
                if message['type'] == 'TRANSFER':
                    print("Received transfer instruction from the server.")
                    # Extract the session information
                    session_info = message['session']
                    session_id = session_info['session_id']
                    file_path = session_info['file_path']  
                    leecher_public_key = session_info['public_key'] 
                    # this is encoded in base64, since this would be passed as a command line argument, to create a new seeder process
                    leecher_public_key_encoded = base64.urlsafe_b64encode(leecher_public_key.encode('utf-8')).decode('utf-8')

                    # Pass the session ID and file path to the method that handles the transfer (starts a new seeder process)
                    self.handle_transfer_instruction(session_id, file_path, leecher_public_key_encoded)
        except Exception as e:
            print(f"Error while listening for instructions: {e}")
        finally:
            self.client_socket.close()

# This class is responsible for handling the file system events and is a subclass of FileSystemEventHandler
class Handler(FileSystemEventHandler):
    def __init__(self, client_socket, public_key):
        self.client_socket = client_socket
        self.public_key = public_key    
        self.public_key_decoded = public_key.decode('utf-8')  # This is there to implement the signature verification in the future

    def send_message(self, action, filepath):
        # Extract filename and size from filepath
        filename = os.path.basename(filepath)
        if action == 'ADD':
            filesize = os.path.getsize(filepath)  # Get the size of the file
        else:
            filesize = 0
        # Constructing and sending JSON formatted message (the metadata of the file)
        message = json.dumps({
            'type': action, # action lets the lookup server know if the file is added or deleted within its directory
            'filename': filename,
            'filelocation': filepath,
            'filesize': filesize,  
            'public_key': self.public_key_decoded  # This is there to implement the signature verification in the future

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
    # This is called by the client_gui when the user clicks the Launch Monitor button
    # This is called using the command line arguments by the client_gui
    if len(sys.argv) != 2:
        print("Usage: python folder_monitor.py <directory_to_watch>")
        sys.exit(1)
    
    directory_to_watch = sys.argv[1]
    # Server IP address and port number hosted on Google Cloud Platform
    SERVER_HOST = '35.224.31.170'     
    SERVER_PORT = 65420     
    # Create a watcher object and start it         
    w = Watcher((SERVER_HOST, SERVER_PORT), directory_to_watch)
    w.run()
