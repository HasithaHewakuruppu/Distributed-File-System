# seeder.py 

import socket
import os
import sys
from tqdm import tqdm 
import base64
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
import time

def send_file_to_server(session_id, file_path, private_key_base64, public_key_base64):
    SERVER_HOST = '35.224.31.170'
    SERVER_PORT = 65410
    buffer_size = 1024  # Match this with the relay server setting

    # Unicode check mark and cross symbols for status updates
    check_mark = '\u2713'
    cross_mark = '\u274C'

    # Decode the base64-encoded RSA keys
    private_key = RSA.import_key(base64.urlsafe_b64decode(private_key_base64))
    public_key = RSA.import_key(base64.urlsafe_b64decode(public_key_base64))

    # Generate AES key and IV
    aes_key = get_random_bytes(16)  # AES-128
    iv = get_random_bytes(AES.block_size)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((SERVER_HOST, SERVER_PORT))
            initial_message = f"seeder,{session_id},{os.path.basename(file_path)}"
            sock.sendall(initial_message.encode('utf-8'))

            # Wait for the server to request file size
            command = sock.recv(buffer_size).decode('utf-8')
            if command == "START":

                # Encrypt and send the AES key and IV
                cipher_rsa = PKCS1_OAEP.new(public_key)
                encrypted_aes_key = cipher_rsa.encrypt(aes_key)
                encrypted_iv = cipher_rsa.encrypt(iv)
                sock.sendall(base64.urlsafe_b64encode(encrypted_aes_key + encrypted_iv))
                print(f"AES key and IV have been sent  {check_mark}")
                time.sleep(0.1) # add small delay

                # Send the file size first
                filesize = os.path.getsize(file_path)
                sock.sendall(str(filesize).encode('utf-8'))
                print(f"File size has been sent.  {check_mark}")

                # Wait for the leecher to signal readiness
                signal = sock.recv(buffer_size).decode('utf-8')
                if signal != "READY":
                    raise Exception("Leecher not ready to receive the file.")
            
                # Encrypt the entire file with AES
                print("Encrypting the file...")
                cipher_aes = AES.new(aes_key, AES.MODE_CFB, iv)
                with open(file_path, 'rb') as f:
                    encrypted_content = cipher_aes.encrypt(f.read())
                
                # Send the encrypted file in chunks
                print(f"Sending encrypted file {file_path}...")
                progress = tqdm(total=filesize, unit='B', unit_scale=True, desc="Uploading")

                # This should be sent in p2p now using WebRTC
                total_sent = 0  
                while total_sent < filesize:
                    chunk = encrypted_content[total_sent:total_sent+buffer_size] 
                    sock.sendall(chunk)  
                    bytes_sent = len(chunk)  
                    total_sent += bytes_sent 
                    progress.update(bytes_sent) 
                progress.close()  
                
                # Wait for a transfer completion message from the server
                confirmation = sock.recv(buffer_size).decode('utf-8')
                if confirmation == "TRANSFER_COMPLETE":
                    print(f"File has been successfully transferred  {check_mark}")
            else:
                print(f"{cross_mark}  Unexpected command from the server:", command)

        except Exception as e:
            print(f"{cross_mark}  Error sending file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        cross_mark = '\u274C'   
        print(f"{cross_mark}  Usage: python seeder.py [session_id] [file_path] [private_key_base64] [public_key_base64]")
        sys.exit(1)

    session_id, file_path, private_key_base64, public_key_base64 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    send_file_to_server(session_id, file_path, private_key_base64, public_key_base64)
    