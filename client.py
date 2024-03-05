# client.py
import socket
import json
import subprocess  

def main():
    # localhost: '127.0.0.1'
    server_host = '127.0.0.1'  # Server's IP address
    server_port = 65420        # Server's port

    # Establish connection to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        client_socket.sendall(b'client')  # Identify this client as a 'client', not a 'seeder'

        print("Connected to the server. Type 'exit' to quit.")
        while True:
            filename = input("Enter filename to search: ")
            if filename.lower() == 'exit':
                break

            message = json.dumps({'type': 'SEARCH', 'filename': filename})
            client_socket.sendall(message.encode('utf-8'))

            response = client_socket.recv(1024).decode('utf-8')
            response_data = json.loads(response)

            if response_data['exists']:
                filesize = response_data['filesize']
                print(f"File exists on server with size {filesize} bytes.")
                download = input("Do you want to download the file? (yes/no): ")
                if download.lower() == 'yes':
                    download_message = json.dumps({'type': 'DOWNLOAD', 'filename': filename})
                    client_socket.sendall(download_message.encode('utf-8'))
                    transfer_response = client_socket.recv(1024).decode('utf-8')
                    transfer_data = json.loads(transfer_response)
                    
                    if transfer_data['type'] == 'TRANSFER':
                        session_info = transfer_data['session']
                        session_id = session_info['session_id']
                        file_path = session_info['file_path']

                        print(f"Starting download with session ID {session_id}.")
                        # For Windows:
                        # subprocess.Popen(['start', 'cmd', '/k', 'python', 'leecher.py', str(session_id), str(file_path)], shell=True)
                        subprocess.Popen(['start', 'cmd', '/k', 'python', 'leecher_hasitha.py', str(session_id), './downloadedfile.txt'], shell=True)
                        
            else:
                print("File does not exist on server.")

if __name__ == "__main__":
    main()
