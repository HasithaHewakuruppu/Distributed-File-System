import socket
import os
import sys
from tqdm import tqdm  

def send_file_to_server(session_id, file_path):
    SERVER_HOST = '35.224.31.170'
    SERVER_PORT = 65410
    buffer_size = 1024  # Match this with the relay server setting
    
    # read the seeder_private_key.pem file and leeche_public_key.pem file
    # the private key is used to sign the file and the public key from the leecher is used to encrypt the file
    with open('./keys/seeder_private_key.pem', 'r') as file:
        seeder_private_key = file.read()
    with open('./keys/leecher_public_key.pem', 'r') as file:
        leecher_public_key = file.read()

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
    if len(sys.argv) != 3:
        print("Usage: python seeder.py [session_id] [file_path]")
        print("The arguments provided were: ", sys.argv)
        sys.exit(1)

    session_id, file_path = sys.argv[1], sys.argv[2]
    send_file_to_server(session_id, file_path)
