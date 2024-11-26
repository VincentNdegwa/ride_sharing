import socket
import os
from dotenv import load_dotenv

load_dotenv()

host = os.getenv('HOST')
port = int(os.getenv('PORT'))

def connect_to_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        
        print(client_socket.recv(1024).decode('utf-8'))
        client_socket.send("driver".encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8'))
        name = input()
        client_socket.send(name.encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8')) 
        lat = input()
        client_socket.send(lat.encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8'))
        lon = input()
        client_socket.send(lon.encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8'))  # Confirmation

        # Keep listening for ride requests
        while True:
            try:
                ride_request = client_socket.recv(1024).decode('utf-8')
                if not ride_request:
                    break
                print(ride_request)
                response = input("Enter 'yes' to approve or 'no' to decline: ")
                client_socket.send(response.encode('utf-8'))
            except Exception as e:
                print("Error:", e)
                break

if __name__ == "__main__":
    connect_to_server()
