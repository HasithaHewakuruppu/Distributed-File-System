import socket
import threading
import json

def handle_seeder(connection, address, file_tracker):
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

                        if action == "ADD":
                            file_tracker[filename] = {'seeder': address, 'filelocation': filelocation}
                            print(f"Added file {filename} from {address}")
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
        print(f"Connection closed for {address}")

def handle_client(connection, address, file_tracker):
    print(f"Client connected from {address}")
    try:
        while True:
            data = connection.recv(1024).decode('utf-8')
            if not data:
                break  # No more data from client

            message = json.loads(data)
            action = message['type']
            filename = message['filename']

            if action == "SEARCH":
                # Check if the file exists in the tracker and respond
                response = 'true' if filename in file_tracker else 'false'
                # TODO: Send the file to the client, for now just respond with the status
                connection.sendall(response.encode('utf-8'))
    except Exception as e:
        print(f"Error with {address}: {e}")
    finally:
        connection.close()
        print(f"Connection closed for {address}")

def start_server(host, port):
    file_tracker = {}  # Stores file information

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f"Server listening on {host}:{port}")

        while True:
            client_conn, client_addr = server_socket.accept()
            client_type = client_conn.recv(1024).decode('utf-8')  # Identifying the client type

            if client_type == 'seeder':
                client_thread = threading.Thread(target=handle_seeder, args=(client_conn, client_addr, file_tracker))
                client_thread.start()
            elif client_type == 'client':
                client_thread = threading.Thread(target=handle_client, args=(client_conn, client_addr, file_tracker))
                client_thread.start()
            else:
                print(f"Unknown client type from {client_addr}")
                client_conn.close()

if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 65432
    start_server(HOST, PORT)
