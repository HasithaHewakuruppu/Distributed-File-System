import socket
import json

def main():
    server_host = '127.0.0.1'  # Server's IP address
    server_port = 65432        # Server's port

    # Establish connection to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        # Send an initial message to identify this client as a 'client' not a 'seeder'
        client_socket.sendall(b'client')  # Sending 'client' as bytes

        print("Connected to the server. Type 'exit' to quit.")
        while True:
            # Ask the user for the filename to search
            filename = input("Enter filename to search: ")
            if filename.lower() == 'exit':  # Allow the user to exit the loop
                break

            # Send search query to the server
            message = json.dumps({'type': 'SEARCH', 'filename': filename})
            client_socket.sendall(message.encode('utf-8'))

            # Wait for and then receive the response from the server
            response = client_socket.recv(1024).decode('utf-8')  # Assuming response will be less than 1024 bytes
            # After receiving the response from the server:
            response_data = json.loads(response)

            if response_data['exists']:
                filesize = response_data['filesize']
                print(f"File exists on server with size {filesize} bytes.")
                # Ask the user if they want to download the file
                download = input("Do you want to download the file? (yes/no): ")
                if download.lower() == 'yes':
                    # Send download request to the server
                    download_message = json.dumps({'type': 'DOWNLOAD', 'filename': filename})
                    client_socket.sendall(download_message.encode('utf-8'))
                    # Placeholder for download functionality; assume server sends a confirmation message
                    download_response = client_socket.recv(1024).decode('utf-8')
                    print(download_response)  # Print the server's response
            else:
                print("File does not exist on server.")

if __name__ == "__main__":
    main()
