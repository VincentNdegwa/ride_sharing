import socket
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get host and port from environment variables
host = os.getenv('HOST')
port = int(os.getenv('PORT'))


def handle_interaction(client_socket, role):
    """Handles the common interaction logic between the client and server."""
    client_socket.recv(1024).decode('utf-8')
    client_socket.send(role.encode('utf-8'))

    name = input(client_socket.recv(1024).decode('utf-8'))
    client_socket.send(name.encode('utf-8'))

    lat = input(client_socket.recv(1024).decode('utf-8'))
    client_socket.send(lat.encode('utf-8'))

    lon = input(client_socket.recv(1024).decode('utf-8'))
    client_socket.send(lon.encode('utf-8'))

    print(client_socket.recv(1024).decode('utf-8'))  # Confirmation


def passenger_client():
    """Handles the passenger client logic."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        handle_interaction(client_socket, "passenger")


def driver_client():
    """Handles the driver client logic."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        handle_interaction(client_socket, "driver")

        # Keep listening for ride requests
        while True:
            try:
                ride_request = client_socket.recv(1024).decode('utf-8')
                if not ride_request:
                    break
                print("Ride Request Received:", ride_request)
                response = input("Enter 'yes' to approve or 'no' to decline: ")
                client_socket.send(response.encode('utf-8'))
            except Exception as e:
                print("Error:", e)
                break


if __name__ == "__main__":
    print("Choose your role:")
    print("1. Passenger")
    print("2. Driver")
    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        passenger_client()
    elif choice == "2":
        driver_client()
    else:
        print("Invalid choice. Exiting.")
