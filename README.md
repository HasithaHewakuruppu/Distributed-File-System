# Distributed-File-System
Distributed File System - Group Project 

# Distributed File System Project

This project implements a basic distributed file system using Python. 
It consists of three main components: a server, a seeder, and a client. 

The server tracks the files available from seeders, 
the seeder monitors a designated folder and informs the server about the file changes, 
and the client can query the server to check if a file exists.

## Getting Started

These instructions will help you set up and run the project on your machine.

1) Run the folder_monitor.py if you want to share files with peers.
2) Run the client.py and type in the file you want to search including the file extension. 
3) Then proceed with the prompts to download, just say yes.
4) To test locally you can run folder_monitor.py and then search the folder_monitor.py contents and download them to the Dowloads folder
5) Make sure to make a folder named Downloads within the code directory 

## TODOS
    # should create AES key, this should be sent to the leecher.py via the relay_server.py
    # But the AES key should be encrypted with the public key of the leecher
    # Then the leecher should decrypt it with their private key, to get the AES key created by the seeder
   
    # so there should be some special message that is sent to the relay server to indicate that the seeder is sending the AES key to the leecher
    # once the leeche receives the AES key, it should send a message to the seeder to indicating that it has received the AES key via the relay server
    # once the seeder receives the message from the leecher, it should start encrypting the file chunks with the AES key and send it to the leecher via the relay server
    # the leecher should then decrypt the file chunks with the AES key to get the original file


## Message for David

1) Currenty the file sharing is done through a relay server.
2) Which is not scalable, ideally file sharing should be p2p.
3) You can try implementing p2p if you have time.
4) You can try other UDP hope punching or WebRTC (not sure if WebRTC is possible since we are not in the web)
