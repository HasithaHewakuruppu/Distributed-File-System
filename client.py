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
            print("File exists on server:" if response == 'true' else "File does not exist on server.")

if __name__ == "__main__":
    main()
