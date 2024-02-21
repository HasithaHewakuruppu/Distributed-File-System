# Distributed-File-System
Distributed File System - Group Project 

# Distributed File System Project

This project implements a basic distributed file system using Python. 
It consists of three main components: a server, a seeder, and a client. 

The server tracks the files available from seeders, 
the seeder monitors a designated folder and informs the server about the file changes, 
and the client can query the server to check if a file exists.

## Getting Started

These instructions will help you set up and run the project on your local machine for development and testing purposes.

1) Run the server code in a terminal
2) Create a folder called the DesignatedFolder in the same directory
3) Add some files into the DesignatedFolder
4) Run the seeder code in another terminal
5) Run the client code in another terminal
6) Try requesting a file that is already in the DesignatedFolder
7) Try requesting something not in the DesignatedFolder
8) Try adding, deleting, and renaming contents in the DesignatedFolder
9) Then try asking to see if your expectation of it being in the DesignatedFolder is matched when queried from the client
