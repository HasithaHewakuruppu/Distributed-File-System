# client_wrapper.py 

import socket
import json
import sys
import time
import subprocess  

def search_for_file(server_host, server_port, filename):
    # Establish connection to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        client_socket.sendall(b'client')   # Identify as a 'client'
        time.sleep(0.5)  # Wait for half a second

        # Send search request for the file
        message = json.dumps({'type': 'SEARCH', 'filename': filename}) 
        client_socket.sendall(message.encode('utf-8'))

        # Receive and process the server's response
        response = client_socket.recv(1024).decode('utf-8')
        response_data = json.loads(response)

        # Return a JSON string indicating whether the file exists and its size
        return json.dumps({'exists': response_data['exists'], 'filesize': response_data.get('filesize', 0)})
        

def download_file(server_host, server_port, filename):
    # Similar structure to search_for_file, but requests a file download
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        client_socket.sendall(b'client')  # Identify as a 'client'
        time.sleep(0.5)  # Wait for half a second
        
        # Send download request for the file
        message = json.dumps({'type': 'DOWNLOAD', 'filename': filename})
        client_socket.sendall(message.encode('utf-8'))

        # Receive and process the server's response
        response = client_socket.recv(1024).decode('utf-8')
        response_data = json.loads(response)

        # Check if the transfer process can start
        if response_data['type'] == 'TRANSFER':
            session_info = response_data['session']
            session_id = session_info['session_id']
            file_path = session_info['file_path']

            print(f"Starting download with session ID {session_id}.")
            # For Windows:
            subprocess.Popen(['start', 'cmd', '/k', 'python', 'leecher.py', str(session_id), str(file_path)], shell=True)
            return json.dumps({'success': True, 'session_id': session_id, 'file_path': file_path})
        else:
            return json.dumps({'success': False})

def main():
    # you communicate with this script using command line arguments
    # e.g. python client_wrapper.py search file.txt
    # the output will be a JSON string indicating whether the file exists and its size
    # and 
    # e.g. python client_wrapper.py download file.txt
    # the output will be a JSON string indicating whether the download was successful and the session info
    # plus will trigger the leecher.py to open a new terminal and start downloading the file

    if len(sys.argv) < 3:
        print(json.dumps({'error': 'Insufficient arguments provided'}))
        sys.exit(1)

    command = sys.argv[1].lower()
    filename = sys.argv[2]
    server_host = '127.0.0.1'
    server_port = 65420

    if command == 'search':
        result = search_for_file(server_host, server_port, filename)
        print(result)  # Print out the result as a JSON string
    elif command == 'download':
        result = download_file(server_host, server_port, filename)
        print(result)  # Print out the result as a JSON string
    else:
        print(json.dumps({'error': 'Invalid command provided'}))

if __name__ == '__main__':
    main()
