import socket

# Server configuration
HOST = 'localhost'
PORT = 12345

def connect_to_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))

        print(client_socket.recv(1024).decode('utf-8'))
        client_socket.send("passenger".encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8'))
        name = input()
        client_socket.send(name.encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8'))
        lat = input()
        client_socket.send(lat.encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8'))
        lon = input()
        client_socket.send(lon.encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8'))

if __name__ == "__main__":
    connect_to_server()
