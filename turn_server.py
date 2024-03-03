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

            print(f"Received {client_type} for session {session_id} with file {filename}")

            if session_id not in self.sessions:
                self.sessions[session_id] = {'seeder': None, 'client': None, 'filename': filename}

            if client_type == 'seeder':
                self.sessions[session_id]['seeder'] = connection
                self.check_ready_and_transfer(session_id)
            elif client_type == 'client':
                self.sessions[session_id]['client'] = connection
                self.check_ready_and_transfer(session_id)
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            # You might not want to close the connection immediately in real scenarios
            # connection.close()
            pass

    def check_ready_and_transfer(self, session_id):
        session = self.sessions[session_id]
        if session['seeder'] and session['client']:
            print(f"Starting file transfer for session {session_id}")
            threading.Thread(target=self.transfer_file, args=(session_id,)).start() # this might not be necessary

    def transfer_file(self, session_id):
        session = self.sessions[session_id]
        seeder_conn = session['seeder']
        client_conn = session['client']
        filename = session['filename']

        if seeder_conn and client_conn:
            try:
                # Implement the actual file transfer here
                # Placeholder for file transfer logic
                print(f"Transferring file {filename} in session {session_id}")
                
                pass
            except Exception as e:
                print(f"Error transferring file {filename} in session {session_id}: {e}")
            finally:
                # Close connections after transfer is complete
                seeder_conn.close()
                client_conn.close()
                # Clean up session data
                del self.sessions[session_id]
        else:
            print("Waiting for both seeder and client to be ready for session:", session_id)

if __name__ == "__main__":
    HOST = '127.0.0.2'  # Change as per your server's IP
    PORT = 65433        # Port for file transfers, change if needed
    file_transfer_server = FileTransferServer(HOST, PORT)
    file_transfer_server.start_server()
