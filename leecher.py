# leecher.py

import sys
import socket

def download_file(session_id, file_path):
    SERVER2_HOST = '127.0.0.2'
    SERVER2_PORT = 65433

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((SERVER2_HOST, SERVER2_PORT))
        initial_message = f"client,{session_id},{file_path}"
        sock.sendall(initial_message.encode('utf-8'))

        # Implement the logic to receive the file from the server
        print("File download completed.")

########  DO NOT MODIFY BELOW THIS LINE  ########
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python client_server2_connector.py [session_id]")
        sys.exit(1)

    session_id = sys.argv[1]
    file_path = sys.argv[2]
    download_file(session_id, file_path) # feel free to modify this function
 