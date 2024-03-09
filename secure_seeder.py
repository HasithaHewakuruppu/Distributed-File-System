# secure_seeder.py 

import socket
import os
import sys
from tqdm import tqdm
import base64
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
import time

def send_file_to_server(session_id, file_path, private_key_base64, public_key_base64):
    SERVER_HOST = '35.224.31.170'
    SERVER_PORT = 65410  # Make sure this is the correct port for the relay server
    buffer_size = 1024  # Adjust as necessary

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

            # Wait for the "START" command
            command = sock.recv(buffer_size).decode('utf-8')
            if command != "START":
                raise Exception("Did not receive start command")

            # Encrypt and send the AES key and IV
            cipher_rsa = PKCS1_OAEP.new(public_key)
            encrypted_aes_key = cipher_rsa.encrypt(aes_key)
            encrypted_iv = cipher_rsa.encrypt(iv)
            sock.sendall(base64.urlsafe_b64encode(encrypted_aes_key + encrypted_iv))
            time.sleep(0.1) # add small delay 

            # Send the file size
            filesize = os.path.getsize(file_path)
            sock.sendall(str(filesize).encode('utf-8'))

            # Wait for the leecher to signal readiness
            signal = sock.recv(buffer_size).decode('utf-8')
            if signal != "READY":
                raise Exception("Leecher not ready to receive the file.")

            # Start sending the file content
            cipher_aes = AES.new(aes_key, AES.MODE_CFB, iv)
            with open(file_path, 'rb') as f:
                progress = tqdm(total=filesize, unit='B', unit_scale=True, desc="Uploading")
                while True:
                    chunk = f.read(buffer_size)
                    if not chunk:
                        break
                    encrypted_chunk = cipher_aes.encrypt(chunk)

                    # Sign the encrypted chunk (optional, if you want integrity checks)
                    # hasher = SHA256.new(encrypted_chunk)
                    # signature = pkcs1_15.new(private_key).sign(hasher)
                    # final_message = base64.urlsafe_b64encode(encrypted_chunk + signature)

                    # without signature
                    final_message = base64.urlsafe_b64encode(encrypted_chunk)
                    sock.sendall(final_message)

                    # Update progress bar
                    progress.update(len(chunk))
                progress.close()

            # Wait for confirmation of complete transfer
            confirmation = sock.recv(buffer_size).decode('utf-8')
            if confirmation == "TRANSFER_COMPLETE":
                print("File has been successfully transferred.")
            else:
                raise Exception("File transfer was not confirmed.")

        except Exception as e:
            print(f"Error during file transfer: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python seeder.py [session_id] [file_path] [private_key_base64] [public_key_base64]")
        sys.exit(1)

    session_id, file_path, private_key_base64, public_key_base64 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    send_file_to_server(session_id, file_path, private_key_base64, public_key_base64)
