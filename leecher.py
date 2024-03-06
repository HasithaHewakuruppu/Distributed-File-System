import socket
import sys
from tqdm import tqdm  # Import tqdm for the progress bar

def download_file_from_server(session_id, save_path):
    SERVER_HOST = '35.224.31.170'
    SERVER_PORT = 65410
    buffer_size = 1024  # Match this with the relay server setting

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((SERVER_HOST, SERVER_PORT))
            initial_message = f"client,{session_id},requested_file"
            sock.sendall(initial_message.encode('utf-8'))

            # Receive the filesize from the server
            filesize = int(sock.recv(buffer_size).decode('utf-8'))

            # Signal the server that the leecher is ready to receive the file
            sock.sendall(b"READY")

            # Initialize progress bar
            progress = tqdm(total=filesize, unit='B', unit_scale=True, desc="Downloading")

            # Start receiving the file
            with open(save_path, 'wb') as f:
                total_received = 0
                while total_received < filesize:
                    bytes_read = sock.recv(buffer_size)
                    if not bytes_read:
                        break  # No more data from the server
                    f.write(bytes_read)
                    total_received += len(bytes_read)
                    # Update the progress bar
                    progress.update(len(bytes_read))

            # Close the progress bar once the file is fully received
            progress.close()

            # Confirm file was received completely
            if total_received == filesize:
                print(f"File successfully downloaded to {save_path}.")
            else:
                print("There was an error downloading the file.")

        except Exception as e:
            print(f"Error downloading file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python leecher.py [session_id] [save_path]")
        sys.exit(1)

    session_id, save_path = sys.argv[1], sys.argv[2]
    download_file_from_server(session_id, save_path)
