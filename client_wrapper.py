# client_wrapper.py 

import socket
import json
import sys
import time
import subprocess
from Crypto.PublicKey import RSA

def generate_rsa_keys():
    # Generate RSA key pair
    key_pair = RSA.generate(2048)
    public_key = key_pair.publickey().exportKey()
    private_key = key_pair.exportKey()
    # Decode keys to string
    public_key_decoded = public_key.decode('utf-8')
    private_key_decoded = private_key.decode('utf-8')
    # Save the private key to a file
    with open('keys/leecher_private_key.pem', 'w') as file:
        file.write(private_key_decoded)
    return public_key_decoded, private_key_decoded

def search_for_file(server_host, server_port, filename):
    # Establish connection to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        client_socket.sendall(b'client')  # Identify as a 'client'
        time.sleep(0.5)  # Wait for half a second

        # Send search request for the file
        message = json.dumps({'type': 'SEARCH', 'filename': filename}) 
        client_socket.sendall(message.encode('utf-8'))

        # Receive and process the server's response
        response = client_socket.recv(1024).decode('utf-8')
        response_data = json.loads(response)

        # Return a JSON string indicating whether the file exists and its size
        return json.dumps({'exists': response_data['exists'], 'filesize': response_data.get('filesize', 0)})

def download_file(server_host, server_port, filename, path, public_key):
    # Similar structure to search_for_file, but requests a file download
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        client_socket.sendall(b'client')  # Identify as a 'client'
        time.sleep(0.5)  # Wait for half a second
        
        # Send download request for the file
        download_message = json.dumps({'type': 'DOWNLOAD', 'filename': filename, 'public_key': public_key})
        client_socket.sendall(download_message.encode('utf-8'))

        # Receive and process the server's response
        response = client_socket.recv(1024).decode('utf-8')
        response_data = json.loads(response)

        # Check if the transfer process can start
        if response_data['type'] == 'TRANSFER':
            session_info = response_data['session']
            session_id = session_info['session_id']
            seeder_public_key = session_info['public_key']

            # save seeder's public key to file to keys folder as seeder_public_key.pem
            with open('keys/seeder_public_key.pem', 'w') as file:
                file.write(seeder_public_key)
            
            print(f"Starting download with session ID {session_id}.")
            download_path = path + filename
            subprocess.Popen(['start', 'cmd', '/k', 'python', 'leecher.py', str(session_id), download_path], shell=True)
            return json.dumps({'success': True, 'session_id': session_id})
        else:
            return json.dumps({'success': False})

def main():
    if len(sys.argv) < 3:
        print(json.dumps({'error': 'Insufficient arguments provided'}))
        sys.exit(1)

    command = sys.argv[1].lower()
    filename = sys.argv[2]
    download_directory = sys.argv[3] if len(sys.argv) > 3 else './'
    server_host = '35.224.31.170'  # Update to your server's host
    server_port = 65420            # Update to your server's port

    if command == 'search':
        result = search_for_file(server_host, server_port, filename)
        print(result)  # Print out the result as a JSON string
    elif command == 'download':
        public_key, _ = generate_rsa_keys()  # Generate RSA keys and get the public key
        result = download_file(server_host, server_port, filename, download_directory, public_key)  # Pass the download directory as an argument
        print(result)  # Print out the result as a JSON string
    else:
        print(json.dumps({'error': 'Invalid command provided'}))

if __name__ == '__main__':
    main()
