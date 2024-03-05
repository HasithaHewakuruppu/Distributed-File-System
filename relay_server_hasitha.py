# relay_server.py

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
            # Initial message should contain: client type, session ID, filename
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
        finally:
            # connection.close()
            pass

    def check_ready_to_transfer(self, session_id):
        session = self.sessions[session_id]
        if session['seeder'] and session['client']: # checks if both seeder and client are ready
            print(f"Starting file transfer for session {session_id}")
            # call the transfer_file method in another thread, 
            # this will be called by the last person to join the session
            threading.Thread(target=self.transfer_file, args=(session_id,)).start()

    def transfer_file(self, session_id):
        session = self.sessions[session_id]
        seeder_conn = session['seeder']
        client_conn = session['client']
        buffer_size = 1024  # You can adjust the buffer size based on your needs

        try:
            # First, inform the seeder to start sending the file
            seeder_conn.sendall(b"START")
            # Get the expected filesize from the seeder
            filesize_str = seeder_conn.recv(buffer_size).decode('utf-8')
            filesize = int(filesize_str)

            # Inform the leecher about the incoming file and its size
            client_conn.sendall(f"{filesize}".encode('utf-8'))

            # Wait for a signal from leecher indicating readiness to receive file
            signal = client_conn.recv(buffer_size).decode('utf-8')
            if signal != "READY":
                raise Exception("Leecher not ready to receive the file.")

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
            client_conn.sendall(b"TRANSFER_COMPLETE")

        except Exception as e:
            print(f"Error during file transfer for session {session_id}: {e}")
        finally:
            # Cleanup: close connections and remove session information
            seeder_conn.close()
            client_conn.close()
            del self.sessions[session_id]
            print(f"Transfer session {session_id} closed.")


    def get_file_size_from_seeder(self, seeder_conn):
        seeder_conn.sendall(b"SIZE")
        filesize = int(seeder_conn.recv(1024).decode('utf-8'))  # Assuming the seeder sends back the size
        return filesize

if __name__ == "__main__":
    HOST = '127.0.0.2'  
    PORT = 65433        
    file_transfer_server = FileTransferServer(HOST, PORT)
    file_transfer_server.start_server()
