import sys
import socket

def upload_file(session_id, file_path):
    SERVER2_HOST = '127.0.0.2'
    SERVER2_PORT = 65433
    print(f"Uploading {file_path} to Server 2 with session ID {session_id}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((SERVER2_HOST, SERVER2_PORT))
        initial_message = f"seeder,{session_id},{file_path}"
        sock.sendall(initial_message.encode('utf-8'))

        # Here, implement the logic to read the file and send it to the server
        print("File upload completed.")


########  DO NOT MODIFY BELOW THIS LINE  ########
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python seeder_server2_connector.py [session_id] [file_path]")
        sys.exit(1)

    session_id = sys.argv[1]
    file_path = sys.argv[2]
    upload_file(session_id, file_path) # feel free to modify this function
