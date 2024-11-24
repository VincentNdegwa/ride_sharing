import socket

# Server configuration
HOST = 'localhost'
PORT = 12345

def connect_to_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))

        # Identify as a passenger
        client_socket.send("passenger".encode('utf-8'))

        # Send passenger details
        print(client_socket.recv(1024).decode('utf-8'))  # "Enter your name:"
        name = input("Enter your name: ")
        client_socket.send(name.encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8'))  # "Enter your pickup latitude:"
        lat = input("Enter your pickup latitude: ")
        client_socket.send(lat.encode('utf-8'))

        print(client_socket.recv(1024).decode('utf-8'))  # "Enter your pickup longitude:"
        lon = input("Enter your pickup longitude: ")
        client_socket.send(lon.encode('utf-8'))

        # Receive driver assignment or unavailability message
        print(client_socket.recv(1024).decode('utf-8'))

if __name__ == "__main__":
    connect_to_server()
