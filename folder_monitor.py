import time
import socket
import json
import os  
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess 
import threading

class Watcher:
    DIRECTORY_TO_WATCH = "DesignatedFolder"  

    def __init__(self, server_address):
        self.observer = Observer()
        self.server_address = server_address
        self.client_socket = None

    def connect_to_server(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect(self.server_address)
        # Send an initial message to identify this client as a 'seeder'
        self.client_socket.sendall(b'seeder')  # Sending 'seeder' as bytes

    def run(self):
        print("Starting the watcher...")
        self.connect_to_server()  # Establish connection to the server

        # Start listening for instructions in a new thread after connection is established
        instructions_thread = threading.Thread(target=self.listen_for_instructions)
        instructions_thread.start()

        event_handler = Handler(self.client_socket)
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

    def handle_transfer_instruction(self, session_id, file_path):
        # Start the new process
        print(f"Starting a new process for {file_path} with session ID {session_id}...")
        subprocess.Popen(['start', 'cmd', '/k', 'python', 'seeder.py', str(session_id), str(file_path)], shell=True)
        #subprocess.Popen(['python', 'seeder.py', session_id, file_path])

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
                    file_path = session_info['file_path']  # Use the file path provided by Server 1

                    # Pass the session ID and file path to the method that handles the transfer
                    self.handle_transfer_instruction(session_id, file_path)
        except Exception as e:
            print(f"Error while listening for instructions: {e}")
        finally:
            self.client_socket.close()

class Handler(FileSystemEventHandler):
    def __init__(self, client_socket):
        self.client_socket = client_socket

    def send_message(self, action, filepath):
        # Extract filename and size from filepath
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)  # Get the size of the file
        # Constructing and sending JSON formatted message
        message = json.dumps({
            'type': action,
            'filename': filename,
            'filelocation': filepath,
            'filesize': filesize  # Add the file size here
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
    SERVER_HOST = '127.0.0.1'  # Server's IP address
    SERVER_PORT = 65432        # Server's port
    w = Watcher((SERVER_HOST, SERVER_PORT))
    w.run()
