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

    # Decode the base64-encoded RSA keys
    private_key = RSA.import_key(base64.urlsafe_b64decode(private_key_base64))
    public_key = RSA.import_key(base64.urlsafe_b64decode(public_key_base64))

    # Generate AES key and IV
    aes_key = get_random_bytes(16)  # AES-128
    iv = get_random_bytes(AES.block_size)

    # should create AES key, this should be sent to the leecher.py via the relay_server.py
    # But the AES key should be encrypted with the public key of the leecher
    # Then the leecher should decrypt it with their private key, to get the AES key created by the seeder
   
    # so there should be some special message that is sent to the relay server to indicate that the seeder is sending the AES key to the leecher
    # once the leeche receives the AES key, it should send a message to the seeder to indicating that it has received the AES key via the relay server
    # once the seeder receives the message from the leecher, it should start encrypting the file chunks with the AES key and send it to the leecher via the relay server
    # the leecher should then decrypt the file chunks with the AES key to get the original file

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
                print("AES key and IV have been sent.")
                time.sleep(0.1) # add small delay

                # Send the file size first
                filesize = os.path.getsize(file_path)
                sock.sendall(str(filesize).encode('utf-8'))
                print("File size has been sent.")

                # Wait for the leecher to signal readiness
                signal = sock.recv(buffer_size).decode('utf-8')
                if signal != "READY":
                    raise Exception("Leecher not ready to receive the file.")
            
                # Encrypt the entire file with AES
                cipher_aes = AES.new(aes_key, AES.MODE_CFB, iv)

                print(f"Sending {os.path.basename(file_path)}...")
                # Start sending the file content
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
                    print("File has been successfully transferred.")
            else:
                print("Unexpected command from the server:", command)

        except Exception as e:
            print(f"Error sending file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python seeder.py [session_id] [file_path] [private_key_base64] [public_key_base64]")
        sys.exit(1)

    session_id, file_path, private_key_base64, public_key_base64 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    send_file_to_server(session_id, file_path, private_key_base64, public_key_base64)