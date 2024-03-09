# secure_relay_server.py

import socket
import threading

class FileTransferServer:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.sessions = {}  # key: session_id, value: dict with seeder, client, filename

    def start_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"File Transfer Server is listening on {self.host}:{self.port}")

            while True:
                client_conn, client_addr = server_socket.accept()
                print(f"Connection from {client_addr}")
                threading.Thread(target=self.handle_connection, args=(client_conn,)).start()

    def handle_connection(self, connection):
        try:
            initial_message = connection.recv(1024).decode('utf-8')
            client_type, session_id, filename = initial_message.split(',')

            print(f"Received {client_type} for session {session_id}")

            if session_id not in self.sessions:
                self.sessions[session_id] = {'seeder': None, 'client': None, 'filename': filename}

            if client_type == 'seeder':
                self.sessions[session_id]['seeder'] = connection
                self.check_ready_to_transfer(session_id)
            elif client_type == 'client':
                self.sessions[session_id]['client'] = connection
                self.check_ready_to_transfer(session_id)
        except Exception as e:
            print(f"Error handling connection: {e}")

    def check_ready_to_transfer(self, session_id):
        session = self.sessions[session_id]
        if session['seeder'] and session['client']:
            print(f"Starting file transfer for session {session_id}")
            threading.Thread(target=self.transfer_file, args=(session_id,)).start()

    def transfer_file(self, session_id):
        session = self.sessions[session_id]
        seeder_conn = session['seeder']
        client_conn = session['client']
        buffer_size = 1024  # Buffer size can be adjusted as necessary

        try:
            seeder_conn.sendall(b"START")

            # Relay the encrypted AES key and IV from the seeder to the leecher
            encrypted_keys_message = seeder_conn.recv(buffer_size)
            client_conn.sendall(encrypted_keys_message)  # Send AES key and IV to leecher

            # Relay the file size from the seeder to the leecher
            filesize = seeder_conn.recv(buffer_size).decode('utf-8')
            client_conn.sendall(filesize.encode('utf-8'))

            # Wait for the leecher to signal readiness
            signal = client_conn.recv(buffer_size).decode('utf-8')
            if signal != "READY":
                raise Exception("Leecher not ready to receive the file.")
            
            # let the seeder know the leecher is ready
            seeder_conn.sendall(b"READY")

            # Transfer file data from seeder to leecher
            total_sent = 0
            while total_sent < int(filesize):
                chunk = seeder_conn.recv(buffer_size)
                if not chunk:
                    break  # End of file
                client_conn.sendall(chunk)
                total_sent += len(chunk)

            # Signal completion of transfer to both seeder and leecher
            seeder_conn.sendall(b"TRANSFER_COMPLETE")
            # client_conn.sendall(b"TRANSFER_COMPLETE")

        except Exception as e:
            print(f"Error during file transfer for session {session_id}: {e}")
        finally:
            # Clean up: close connections and delete session info
            seeder_conn.close()
            client_conn.close()
            del self.sessions[session_id]
            print(f"Transfer session {session_id} closed.")

if __name__ == "__main__":
    HOST = ''  
    PORT = 65410        
    file_transfer_server = FileTransferServer(HOST, PORT)
    file_transfer_server.start_server()
