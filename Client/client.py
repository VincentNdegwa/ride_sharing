import socket
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get host and port from environment variables
host = os.getenv('HOST')
port = int(os.getenv('PORT'))


def driver_client(client_socket):
    # handle_interaction(client_socket, "driver")

    while True:
        try:
            ride_request = client_socket.recv(1024).decode('utf-8')
            if "Enter your current latitude: " in ride_request:
                lat = input(ride_request)
                client_socket.send(lat.encode('utf-8'))
            if "Enter your current longitude: " in ride_request:
                lon = input(ride_request)
                client_socket.send(lon.encode('utf-8'))
            if "You are now available for ride requests." in ride_request:
                print(ride_request)
            else:
                print(ride_request)
        except Exception as e:
            print(f"Error in driver logic: {e}")
            break


def passenger_client(client_socket):
    while True:
        try:
            ride_request = client_socket.recv(1024).decode('utf-8')
            if "Enter your current latitude: " in ride_request:
                lat = input(ride_request)
                client_socket.send(lat.encode('utf-8'))
            if "Enter your current longitude: " in ride_request:
                lon = input(ride_request)
                client_socket.send(lon.encode('utf-8'))
            else:
                print(ride_request)
        except Exception as e:
            print(f"Error in driver logic: {e}")
            break


def handle_authenticate(client_socket):
    while True:
        response = client_socket.recv(1024).decode('utf-8').strip()
        print("Received:", response)
        
        if "Do you want to login or register? (login/register)" in response:
            choice = input()  # Get choice from the user (login or register)
            client_socket.send(choice.encode('utf-8'))  # Send the choice to the server
        
        elif "Enter username:" in response:
            username = input()  # Get username from user
            client_socket.send(username.encode('utf-8'))  # Send username to server
        
        elif "Enter password:" in response:
            password = input()  # Get password from user
            client_socket.send(password.encode('utf-8'))  # Send password to server
        
        elif "Select your role (driver or passenger):" in response:
            role = input()  # Get role from user (driver or passenger)
            client_socket.send(role.encode('utf-8'))  # Send role to server
        
        elif "Login successful!" in response:
            print("Login successful!")
            return  # Authentication successful, exit loop
        
        elif "Invalid credentials. Try again." in response:
            print("Invalid credentials. Try again...")
            continue  # Retry login
        
        elif "Username already exists. Try again." in response:
            print("Username already exists. Try again...")
            continue  # Retry registration
        
        elif "Invalid choice. Try again." in response:
            print("Invalid choice. Try again...")
            continue  # Retry login or registration choice
        
        elif response in ["driver", "passenger"]:
            print(f"Your role is: {response}")
            return response
        
        else:
            print(f"Unexpected response: {response}")
            break


if __name__ == "__main__":
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        try:
            client_socket.connect((host, port))
            role = handle_authenticate(client_socket) 
            print("Authentication successful")

            if role.lower() == "driver":
                driver_client(client_socket)
            elif role.lower() == "passenger":
                passenger_client(client_socket)
            else:
                print("Invalid role. Disconnecting.")

        except Exception as e:
            print(f"An error occurred: {e}")
