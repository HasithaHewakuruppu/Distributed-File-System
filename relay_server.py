##### FEEL FREE TO MODIFY THIS CODE AS YOU SEE FIT, ENTIRELY IF YOU WANT #####

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
            # call the transfer_file method, this will be called by the last person to join the session

    def transfer_file(self, session_id):
        session = self.sessions[session_id]
        seeder_conn = session['seeder']
        client_conn = session['client']
        filename = session['filename']

        # this is where the server would message the seeder to start sending the file to the server
        # once the server receives the file, it would terminate the connection with the seeder
        # and then the server would send the file to the client
        # once the client receives the file, it would terminate the connection with the server
        # and then the server would remove the session from the sessions dictionary

if __name__ == "__main__":
    HOST = '127.0.0.2'  
    PORT = 65433        
    file_transfer_server = FileTransferServer(HOST, PORT)
    file_transfer_server.start_server()
