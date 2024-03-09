# secure_leecher.py

import socket
import sys
from tqdm import tqdm
import base64
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
# from Crypto.Signature import pkcs1_15
# from Crypto.Hash import SHA256

def download_file_from_server(session_id, save_path, private_key_base64, public_key_base64):
    SERVER_HOST = '35.224.31.170'
    SERVER_PORT = 65410  # Ensure this matches the relay server port
    buffer_size = 1024  # Adjust as necessary

    # Decode the base64-encoded RSA keys
    private_key = RSA.import_key(base64.urlsafe_b64decode(private_key_base64))
    public_key = RSA.import_key(base64.urlsafe_b64decode(public_key_base64))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((SERVER_HOST, SERVER_PORT))
            # Send initial request: "client,{session_id},requested_file"
            initial_message = f"client,{session_id},requested_file"
            sock.sendall(initial_message.encode('utf-8'))

            # Wait to receive the encrypted AES key and IV
            encrypted_keys_message = base64.urlsafe_b64decode(sock.recv(buffer_size))
            cipher_rsa = PKCS1_OAEP.new(private_key)
            encrypted_aes_key, encrypted_iv = encrypted_keys_message[:256], encrypted_keys_message[256:]
            aes_key = cipher_rsa.decrypt(encrypted_aes_key)
            iv = cipher_rsa.decrypt(encrypted_iv)

            # Receive the file size
            filesize = int(sock.recv(buffer_size).decode('utf-8'))
            # Signal ready to receive the file
            sock.sendall(b"READY")

            # Initialize progress bar
            progress = tqdm(total=filesize, unit='B', unit_scale=True, desc="Downloading")
            cipher_aes = AES.new(aes_key, AES.MODE_CFB, iv)

            total_received = 0
            with open(save_path, 'wb') as f:
                while total_received < filesize:
                    encrypted_data = base64.urlsafe_b64decode(sock.recv(buffer_size))
                    # encrypted_chunk, signature = encrypted_data[:-256], encrypted_data[-256:]  # Extract chunk and signature

                    # Try commenting or removing the signature verification part:
                    # hasher = SHA256.new(encrypted_chunk)
                    # try:
                    #     pkcs1_15.new(public_key).verify(hasher, signature)
                    # except (ValueError, TypeError):
                    #     print("The signature is not valid.")

                    # If signature is valid, decrypt and write chunk (Now we just decrypt and write without checking)
                    chunk = cipher_aes.decrypt(encrypted_data)
                    f.write(chunk)
                    total_received += len(chunk)
                    progress.update(len(chunk))

            progress.close()

            # Confirm file was fully received
            if total_received == filesize:
                print(f"File successfully downloaded to {save_path}.")
            else:
                print("There was an error downloading the file.")

        except Exception as e:
            print(f"Error downloading file: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python leecher.py [session_id] [save_path] [private_key_base64] [public_key_base64]")
        sys.exit(1)

    session_id, save_path, private_key_base64, public_key_base64 = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    download_file_from_server(session_id, save_path, private_key_base64, public_key_base64)
