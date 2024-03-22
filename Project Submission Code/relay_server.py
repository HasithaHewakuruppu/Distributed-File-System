# relay_server.py

import socket
import threading

class FileTransferServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sessions = {}  # session_id: {seeder: conn, client: conn, filename: str}, maintains the unique session between seeder and leecher

    # Start the server binding to port, and listen for incoming connections
    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen()
            print(f"File Transfer Server is listening on {self.host}:{self.port}")

            while True:
                client_conn, client_addr = server_socket.accept()
                print(f"Connection from {client_addr}")
                # Create a new thread to handle each incoming connection
                threading.Thread(target=self.handle_connection, args=(client_conn,)).start()

    def handle_connection(self, connection):
        try:
            # Initial message from should contain: client type, session ID, filename
            # This message is sent by both seeder and client/leecher
            initial_message = connection.recv(1024).decode('utf-8')
            client_type, session_id, filename = initial_message.split(',')

            print(f"Received {client_type} for session {session_id}")

            # Create a new session if it doesn't exist, this is created by the first person to join the session
            if session_id not in self.sessions:
                self.sessions[session_id] = {'seeder': None, 'client': None, 'filename': filename}

            # Each connecting user type saves their connection in the session dictionary
            if client_type == 'seeder':
                self.sessions[session_id]['seeder'] = connection
                self.check_ready_to_transfer(session_id) # checks if both seeder and client are connected to the relay server
            elif client_type == 'client':
                self.sessions[session_id]['client'] = connection
                self.check_ready_to_transfer(session_id) # checks if both seeder and client are connected to the relay server
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            # connection.close()
            pass

    def check_ready_to_transfer(self, session_id):
        session = self.sessions[session_id]
         # If both the seeder and leecher are connected, 
         # Then it starts the file transfer as a new thread by calling the transfer_file method
        if session['seeder'] and session['client']: 
            print(f"Starting file transfer for session {session_id}")
            # this will be called by the last person to join the session
            threading.Thread(target=self.transfer_file, args=(session_id,)).start()

    def transfer_file(self, session_id):
        # extract the seeder and client connections from the session
        session = self.sessions[session_id]
        seeder_conn = session['seeder']
        client_conn = session['client']
        buffer_size = 1024  

        try:
            # First, inform the seeder to start sending the file, since now both seeder and leecher are connected
            seeder_conn.sendall(b"START")

            # Relay the encrypted AES key and IV from the seeder to the leecher
            print("Waiting for AES key and IV from seeder...")
            encrypted_keys_message = seeder_conn.recv(buffer_size)
            client_conn.sendall(encrypted_keys_message)  # Send AES key and IV to leecher
            print("AES key and IV have been sent to the leecher.")

            # Relay the file size from the seeder to the leecher
            print("Waiting for file size from seeder...")
            filesize_str = seeder_conn.recv(buffer_size).decode('utf-8')
            filesize = int(filesize_str)
            client_conn.sendall(f"{filesize}".encode('utf-8'))
            print(f"File size {filesize} has been sent to the leecher.")

            # Wait for the leecher to signal readiness
            print("Waiting for readiness signal from leecher...")
            signal = client_conn.recv(buffer_size).decode('utf-8')
            if signal != "READY":
                raise Exception("Leecher not ready to receive the file.")
            
            # let the seeder know the leecher is ready
            seeder_conn.sendall(b"READY")
            print("Ready signal has been sent to the seeder.")

            print(f"Transferring {session['filename']}...")
            # Transfer the file from seeder to leecher in chunks
            total_received = 0
            while total_received < filesize:
                chunk = seeder_conn.recv(buffer_size)
                if not chunk:
                    break  # No more data from the seeder
                client_conn.sendall(chunk)
                total_received += len(chunk)

            # Ensure the entire file was transferred
            if total_received != filesize:
                raise Exception("File transfer was incomplete.")

            # Send a completion message to both seeder and leecher
            seeder_conn.sendall(b"TRANSFER_COMPLETE")
            #client_conn.sendall(b"TRANSFER_COMPLETE")

        except Exception as e:
            print(f"Error during file transfer for session {session_id}: {e}")
        finally:
            # Cleanup: close connections and remove session information
            seeder_conn.close()
            client_conn.close()
            del self.sessions[session_id]
            print(f"Transfer session {session_id} closed.")


if __name__ == "__main__":
    HOST = ''                                              # Listen on all incoming IP addresses
    PORT = 65410                                           # Port listening on    
    file_transfer_server = FileTransferServer(HOST, PORT)  # Create a FileTransferServer object
    file_transfer_server.start_server()
