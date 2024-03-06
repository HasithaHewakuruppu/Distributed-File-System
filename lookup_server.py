# lookup_server.py 

import socket
import threading
import json
import uuid

def handle_seeder(connection, address, file_tracker, active_seeders):
    active_seeders[address] = connection  # Store the seeder's connection
    print(f"Seeder connected from {address}")
    try:
        buffer = ""
        while True:
            data = connection.recv(1024).decode('utf-8')
            if not data:
                break  # No more data from seeder

            buffer += data  # Append new data to buffer
            while '\n' in buffer:  # Check if there are complete messages separated by newlines
                message, buffer = buffer.split('\n', 1)  # Split on the first newline
                if message:  # Check if the message is not empty
                    try:
                        # Parse the complete message from JSON format
                        parsed_message = json.loads(message)
                        action = parsed_message['type']
                        filename = parsed_message['filename']
                        filelocation = parsed_message['filelocation']
                        public_key = parsed_message['public_key']

                        if action == "ADD":
                            filesize = parsed_message['filesize']  # Retrieve the filesize from the message
                            file_tracker[filename] = {
                                'seeder': address,
                                'filelocation': filelocation,
                                'filesize': filesize,  # Store the filesize in the file_tracker
                                'public_key': public_key  # Store the public key in the file_tracker
                            }
                            print(f"Added file {filename} with size {filesize} bytes from {address}")
                        elif action == "DELETE":
                            if filename in file_tracker:
                                del file_tracker[filename]
                                print(f"Deleted file {filename} from tracker")
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error: {e}")
    except Exception as e:
        print(f"Error with {address}: {e}")
    finally:
        # Remove all files associated with this seeder
        keys_to_remove = [key for key, value in file_tracker.items() if value['seeder'] == address]
        for key in keys_to_remove:
            del file_tracker[key]
        print(f"Removed all files associated with {address}")
        connection.close()
        active_seeders[address] = connection
        print(f"Connection closed for {address}")

def handle_client(connection, address, file_tracker, active_seeders):
    print(f"Client connected from {address}")
    try:
        while True:
            data = connection.recv(1024).decode('utf-8')
            if not data:
                break

            message = json.loads(data)
            action = message['type']
            filename = message['filename']

            if action == "SEARCH":
                if filename in file_tracker:
                    file_info = file_tracker[filename]
                    response = json.dumps({'exists': True, 'filesize': file_info['filesize']})
                else:
                    response = json.dumps({'exists': False})
                connection.sendall(response.encode('utf-8'))

            elif action == "DOWNLOAD":
                if filename in file_tracker:
                    # Generate a unique session ID for this transfer
                    public_key = message['public_key']    
                    session_id = generate_unique_session_id()  
                    file_info = file_tracker[filename]
                   
                    session_info_seeder = {'session_id': session_id, 'file_path': file_info['filelocation'], 'public_key': public_key}
                    session_info_leecher = {'session_id': session_id, 'file_path': file_info['filelocation'], 'public_key': file_info['public_key']}
                    # Inform the client about session details
                    connection.sendall(json.dumps({'type': 'TRANSFER', 'session': session_info_leecher}).encode('utf-8'))
                    # Inform the folder_monitor about session details
                    seeder_addr = file_info['seeder']
                    if seeder_addr in active_seeders:  
                        seeder_connection = active_seeders[seeder_addr]
                        seeder_connection.sendall(json.dumps({'type': 'TRANSFER', 'session': session_info_seeder}).encode('utf-8'))

    except Exception as e:
        print(f"Error with {address}: {e}")
    finally:
        connection.close()
        print(f"Connection closed for {address}")

def generate_unique_session_id():
    # Generate a random UUID (UUID4)
    session_id = uuid.uuid4()
    return str(session_id)

def start_server(host, port):
    file_tracker = {}  # Stores file information
    active_seeders = {}  # Maps seeder addresses to their socket connections

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"Server listening on {host}:{port}")

        while True:
            client_conn, client_addr = server_socket.accept()
            print(f"New connection from {client_addr}")
            client_type = client_conn.recv(1024).decode('utf-8')  # Identifying the client type
            print(f"Received initial message: {client_type}")

            if client_type == 'seeder':
                client_thread = threading.Thread(target=handle_seeder, args=(client_conn, client_addr, file_tracker, active_seeders))
                client_thread.start()
            elif client_type == 'client':
                client_thread = threading.Thread(target=handle_client, args=(client_conn, client_addr, file_tracker, active_seeders))
                client_thread.start()
            else:
                print(f"Unknown client type from {client_addr}")
                client_conn.close()

if __name__ == "__main__":
    HOST = ''
    PORT = 65420
    start_server(HOST, PORT)
