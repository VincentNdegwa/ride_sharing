import socket

# Server configuration
HOST = 'localhost'
PORT = 12345

def connect_to_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))

        # Identify as a driver
        client_socket.send("driver".encode('utf-8'))

        # Send driver details
        print(client_socket.recv(1024).decode('utf-8'))  # "Enter your name:"
        name = input("Enter your name: ")
        client_socket.send(name.encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8'))  # "Enter your current latitude:"
        lat = input("Enter your current latitude: ")
        client_socket.send(lat.encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8'))  # "Enter your current longitude:"
        lon = input("Enter your current longitude: ")
        client_socket.send(lon.encode('utf-8'))

        # Receive confirmation of availability
        print(client_socket.recv(1024).decode('utf-8'))

if __name__ == "__main__":
    connect_to_server()
