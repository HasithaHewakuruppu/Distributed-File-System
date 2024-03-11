import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import socket
import json
import subprocess  
from Crypto.PublicKey import RSA
import base64
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def choose_directory():
    directory = filedialog.askdirectory()
    downloadLocationEntry.delete(0, tk.END)  # Clear any previous value
    downloadLocationEntry.insert(0, directory)
    # Write the chosen directory to the second line of a text file
    try:
        with open("Config.txt", 'r+') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if line.startswith("DownloadPath="):
                    lines[i] = "DownloadPath= " + directory + '\n'
                    break      
            file.seek(0)
            file.writelines(lines)
    except Exception as e:
        print(f"An error occurred: {e}")


def choose_monitor_directory():
    directory = filedialog.askdirectory()
    folderToMonitorEntry.delete(0, tk.END)  # Clear any previous value
    folderToMonitorEntry.insert(0, directory)
    # Write the chosen directory to the second line of a text file
    try:
        with open("Config.txt", 'r+') as file:
            lines = file.readlines()
            for i, line in enumerate(lines):
                if line.startswith("FolderMonitorPath="):
                    lines[i] = "FolderMonitorPath= " + directory + '\n'
                    break      
            file.seek(0)
            file.writelines(lines)
    except Exception as e:
        print(f"An error occurred: {e}")

def choose_file():
    file_path = filedialog.askopenfilename()
    fileToSearchEntry.delete(0, tk.END)  # Clear any previous value
    fileToSearchEntry.insert(0, file_path)

def searchAndDownloadFile(filename, downloadDirectory):
    if not os.path.exists(downloadDirectory):
        messagebox.showinfo("ERROR",f"The directory '{downloadDirectory}' does not exist.")
        return
    # localhost: '127.0.0.1'
    server_host = '35.224.31.170' # Server's IP address
    server_port = 65420           # Server's port
    key_pair = RSA.generate(2048) # Generate new RSA keys
    public_key = key_pair.publickey().exportKey() 
    public_key_decoded = public_key.decode('utf-8')
    private_key = key_pair.exportKey() 
    private_key_encoded = base64.urlsafe_b64encode(private_key).decode('utf-8')

    # Establish connection to the server
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((server_host, server_port))
        client_socket.sendall(b'client')  # Identify this client as a 'client', not a 'seeder'

        message = json.dumps({'type': 'SEARCH', 'filename': filename})
        client_socket.sendall(message.encode('utf-8'))

        response = client_socket.recv(1024).decode('utf-8')
        response_data = json.loads(response)

        if response_data['exists']:
            filesize = response_data['filesize']
            print(f"File exists on server with size {filesize} bytes.")
            result = messagebox.askyesno("File Found", f"The file is located in the server and it's size is {filesize} bytes. Would you like to download it?")
            if result:
                download_message = json.dumps({'type': 'DOWNLOAD', 'filename': filename, 'public_key': public_key_decoded})
                client_socket.sendall(download_message.encode('utf-8'))
                transfer_response = client_socket.recv(1024).decode('utf-8')
                transfer_data = json.loads(transfer_response)
                
                if transfer_data['type'] == 'TRANSFER':
                    session_info = transfer_data['session']
                    session_id = session_info['session_id']
                    seeder_public_key = session_info['public_key']
                    
                    seeder_public_key_encoded = base64.urlsafe_b64encode(seeder_public_key.encode('utf-8')).decode('utf-8')

                    download_file = downloadDirectory + '/' + filename
                    print(f"Starting download with session ID {session_id}.")
                    # For Windows:
                    subprocess.Popen(['start', 'cmd', '/k', 'python', 'leecher.py', str(session_id), str(download_file), private_key_encoded, seeder_public_key_encoded], shell=True)
        else:
            messagebox.showinfo("Error", "File not found in the system...")

def toggleFileMonitor(monitorDirectory):
    if not os.path.exists(monitorDirectory):
        messagebox.showinfo("ERROR",f"The directory '{monitorDirectory}' does not exist.")
        return    
    subprocess.Popen(['start', 'cmd', '/k', 'python', 'folder_monitor_gui.py', monitorDirectory], shell=True)

def initalizeConfig():
    pathVals = ["", ""]
    if os.path.exists("Config.txt"):
        validateConfigFile()
        with open('Config.txt', 'r') as file:
            # Read each line
            for line in file:
                # Check if the line starts with "DownloadPath="
                if line.startswith("DownloadPath="):
                    # Extract the string after "DownloadPath=" and store it in array slot 0
                    pathVals[0] = line.split("=")[1].strip()
                # Check if the line starts with "FolderMonitorPath="
                elif line.startswith("FolderMonitorPath="):
                    # Extract the string after "FolderMonitorPath=" and store it in array slot 1
                    pathVals[1] = line.split("=")[1].strip()
        downloadLocationEntry.insert(0, pathVals[0])
        folderToMonitorEntry.insert(0, pathVals[1])
    else:
        try:
            # Try to open the file in write mode
            with open('Config.txt', 'w') as file:
                file.write("DownloadPath= \nFolderMonitorPath= ")
        except Exception as e:
            print(f"An error occurred: {e}")

def validateConfigFile():
    illegalMod = False
    try:
        with open("Config.txt", 'r+') as file:
            lines = file.readlines()
            if len(lines) < 2:
                illegalMod = True
                with open('Config.txt', 'w') as file:
                    file.write("DownloadPath= \nFolderMonitorPath= ")
            else:
                # Check first line for 'DownloadPath='
                if not lines[0].startswith('DownloadPath='):
                    lines[0] = 'DownloadPath=\n'
                    illegalMod = True
                # Check second line for 'FolderMonitorPath='
                if not lines[1].startswith('FolderMonitorPath='):
                    lines[1] = 'FolderMonitorPath=\n'
                    illegalMod = True
                # Keep only the first two lines
                lines = lines[:2]
                file.seek(0)  # go back to the start of the file
                file.writelines(lines)  # write the modified lines back to the file
                file.truncate()  # remove any remaining content
        if illegalMod:
            messagebox.showinfo("Error", "Config file format invalid, file was reset...")
    except Exception as e:
        print(f"An error occurred: {e}")

# Create the main Tkinter window
root = tk.Tk()
root.title("Distributed File System Client GUI")
root.resizable(False, False)  # Disable window resizing
# Title
title_label = tk.Label(root, text="Distributed File System Client", font=("Helvetica", 16, "bold"))
title_label.grid(row=0, columnspan=3, padx=10, pady=10)

# Directory selection
directory_label = tk.Label(root, text="Download Location:")
directory_label.grid(row=1, column=0, padx=10, pady=10, sticky=tk.W)

downloadLocationEntry = tk.Entry(root, width=50)
downloadLocationEntry.grid(row=1, column=1, padx=10, pady=10)

directory_button = tk.Button(root, text="Search Directory", command=choose_directory)
directory_button.grid(row=1, column=2, padx=10, pady=10)

# File to search selection
file_label = tk.Label(root, text="File to search:")
file_label.grid(row=2, column=0, padx=10, pady=10, sticky=tk.W)

fileToSearchEntry = tk.Entry(root, width=50)
fileToSearchEntry.grid(row=2, column=1, padx=10, pady=10)

file_button = tk.Button(root, text="Search File", command=lambda: searchAndDownloadFile(fileToSearchEntry.get(), downloadLocationEntry.get()))
file_button.grid(row=2, column=2, padx=10, pady=10)

#File Monitor Components
fileMonitorTitle = tk.Label(root, text="Folder Monitor", font=("Helvetica", 10, "bold"))
fileMonitorTitle.grid(row=3, columnspan=3, padx=10, pady=10)

folderToMonitorLabel = tk.Label(root, text="File to monitor:")
folderToMonitorLabel.grid(row=4, column=0, padx=10, pady=10, sticky=tk.W)

folderToMonitorEntry = tk.Entry(root, width=50)
folderToMonitorEntry.grid(row=4, column=1, padx=10, pady=10)

folderToMonitorButton = tk.Button(root, text="Select File to Monitor", command=choose_monitor_directory)
folderToMonitorButton.grid(row=4, column=2, padx=10, pady=10)

activateMonitorButton = tk.Button(root, text="Launch Monitor", command=lambda: toggleFileMonitor(folderToMonitorEntry.get()))
activateMonitorButton.grid(row=5, column=2, padx=10, pady=10)

initalizeConfig()
root.mainloop()