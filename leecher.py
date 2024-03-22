# leecher.py

import socket
import sys
from tqdm import tqdm
import base64
import os  
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA

def download_file_from_server(session_id, save_path, private_key_base64, public_key_base64):
    # Server IP address and port number hosted on Google Cloud Platform
    SERVER_HOST = '35.224.31.170'
    SERVER_PORT = 65410

    # Buffer size for sending and receiving data, including file chunks
    buffer_size = 1024  

    # Unicode check mark and cross symbols for status updates
    check_mark = '\u2713'  
    cross_mark = '\u274C'  

    # Decode the base64-encoded RSA keys from the command-line arguments passed by the folder monitor
    private_key = RSA.import_key(base64.urlsafe_b64decode(private_key_base64))  # This is the private key of the client (one who wants to download the file), this is used in the code below to decrypt the AES key and IV.
    public_key = RSA.import_key(base64.urlsafe_b64decode(public_key_base64))    # NOTE: public_key of the folder monitor was passed, in hopes of verifying the signature of the file, but was never implemented, but if needed can be implemented in the future.

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            # Connect to the server and inform it that this is a leecher/client
            sock.connect((SERVER_HOST, SERVER_PORT))
            initial_message = f"client,{session_id},requested_file"
            sock.sendall(initial_message.encode('utf-8'))
            
            # Wait to receive the encrypted AES key and IV
            # Note this is encrypted using the public key of the client, 
            # The leecher (this file) will decrypt it using its private key, which was passed as a command line argument to it.
            encrypted_keys_message = base64.urlsafe_b64decode(sock.recv(buffer_size))
            cipher_rsa = PKCS1_OAEP.new(private_key)
            encrypted_aes_key, encrypted_iv = encrypted_keys_message[:256], encrypted_keys_message[256:]
            
            # Decrypt the AES key and IV
            aes_key = cipher_rsa.decrypt(encrypted_aes_key)
            iv = cipher_rsa.decrypt(encrypted_iv)
            print(f"AES key and IV have been received  {check_mark}")

            # Receive the filesize from the relay server
            filesize = int(sock.recv(buffer_size).decode('utf-8'))
            print(f"File size: {filesize} bytes to download  {check_mark}")

            # Signal the server that the leecher is ready to receive the file
            sock.sendall(b"READY")
            print(f"Ready to receive the file  {check_mark}")

            # Define paths for encrypted and decrypted files
            file_name, file_extension = os.path.splitext(save_path)
            encrypted_save_path = f"{file_name}_encrypted{file_extension}"

            # Initialize progress bar for downloading
            print(f"Receiving encrypted file...")
            progress = tqdm(total=filesize, unit='B', unit_scale=True, desc="Downloading")
            
            # Start receiving the file and writing it in encrypted form
            with open(encrypted_save_path, 'wb') as f:
                total_received = 0
                while total_received < filesize:
                    bytes_read = sock.recv(buffer_size)
                    if not bytes_read:
                        break
                    f.write(bytes_read)
                    total_received += len(bytes_read)
                    progress.update(len(bytes_read))
            progress.close()
            print(f"Encrypted file successfully downloaded to {encrypted_save_path}  {check_mark}")

            # Now, decrypt the file
            cipher_aes = AES.new(aes_key, AES.MODE_CFB, iv)
            print(f"Decrypting the file to {save_path}...")
            with open(encrypted_save_path, 'rb') as f_encrypted, open(save_path, 'wb') as f_decrypted:
                encrypted_data = f_encrypted.read()
                decrypted_data = cipher_aes.decrypt(encrypted_data)
                f_decrypted.write(decrypted_data)
            print(f"File successfully decrypted  {check_mark}")

        # Handle exceptions 
        except Exception as e:
            print(f"{cross_mark}  Error downloading file: {e}")

if __name__ == "__main__":
    cross_mark = '\u274C'  
    if len(sys.argv) != 5:
        print(f"{cross_mark}  Usage: python leecher.py [session_id] [save_path] [private_key_base64] [public_key_base64]")
        sys.exit(1)

    # The public and private keys are passed as base64-encoded strings to prevent errors when passed as command-line arguments
    # Note all these args are passed by the client (client_gui.py)
    session_id, save_path, private_key_base64, public_key_base64 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    download_file_from_server(session_id, save_path, private_key_base64, public_key_base64)
