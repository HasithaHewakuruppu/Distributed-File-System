import socket
import os
import sys

def send_file_to_server(session_id, file_path):
    SERVER_HOST = '127.0.0.2'
    SERVER_PORT = 65433
    buffer_size = 1024  # Match this with the relay server setting

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((SERVER_HOST, SERVER_PORT))
            initial_message = f"seeder,{session_id},{os.path.basename(file_path)}"
            sock.sendall(initial_message.encode('utf-8'))

            # Wait for the server to request file size
            command = sock.recv(buffer_size).decode('utf-8')
            if command == "START":
                # Send the file size first
                filesize = os.path.getsize(file_path)
                sock.sendall(str(filesize).encode('utf-8'))

                # Then start sending the file content
                with open(file_path, 'rb') as f:
                    while True:
                        bytes_read = f.read(buffer_size)
                        if not bytes_read:
                            break  # File transmission is done
                        sock.sendall(bytes_read)
                
                # Wait for a transfer completion message from the server
                confirmation = sock.recv(buffer_size).decode('utf-8')
                if confirmation == "TRANSFER_COMPLETE":
                    print("File has been successfully transferred to the relay server.")
            else:
                print("Unexpected command from the server:", command)

        except Exception as e:
            print(f"Error sending file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python seeder.py [session_id] [file_path]")
        sys.exit(1)

    session_id, file_path = sys.argv[1], sys.argv[2]
    send_file_to_server(session_id, file_path)
