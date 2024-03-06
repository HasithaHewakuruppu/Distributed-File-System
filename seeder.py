import socket
import os
import sys
from tqdm import tqdm  # Import tqdm for the progress bar

def send_file_to_server(session_id, file_path):
    SERVER_HOST = '35.224.31.170'
    SERVER_PORT = 65410
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
                    # Initialize progress bar
                    progress = tqdm(total=filesize, unit='B', unit_scale=True, desc="Uploading")
                    while True:
                        bytes_read = f.read(buffer_size)
                        if not bytes_read:
                            # File transmission is done
                            progress.close()
                            break
                        sock.sendall(bytes_read)
                        # Update the progress bar
                        progress.update(len(bytes_read))
                
                # Wait for a transfer completion message from the server
                confirmation = sock.recv(buffer_size).decode('utf-8')
                if confirmation == "TRANSFER_COMPLETE":
                    print("File has been successfully transferred to the relay server.")
            else:
                print("Unexpected command from the server:", command)

        except Exception as e:
            print(f"Error sending file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python seeder.py [session_id] [file_path] [private_key] [public_key]")
        print("The arguments provided were: ", sys.argv)
        sys.exit(1)

    # session_id, file_path = sys.argv[1], sys.argv[2]
    session_id, file_path, private_key, public_key = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    send_file_to_server(session_id, file_path)
