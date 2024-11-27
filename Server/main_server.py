import socket
from math import radians, sin, cos, sqrt, atan2
from threading import Thread
from multiprocessing import Process, Queue
import os
from dotenv import load_dotenv
import time

load_dotenv()

host = os.getenv('HOST')
port = int(os.getenv('PORT'))

# Shared queues for workers
passenger_queue = Queue()
driver_queue = Queue()

# In-memory user database for authentication
user_db = {}

driver_status = {}  
def worker_process(passenger_queue, driver_queue):
    while True:
        try:
            if not passenger_queue.empty() and not driver_queue.empty():
                passenger = passenger_queue.get()
                available_drivers = []

                # Check for available drivers
                while not driver_queue.empty():
                    driver = driver_queue.get()
                    driver_name = driver["name"]
                    passenger_name = passenger["name"]

                    # Initialize driver status if not already tracked
                    if driver_name not in driver_status:
                        driver_status[driver_name] = {'available': True, 'rejections': {}}

                    status = driver_status[driver_name]

                    # Check availability and rejection timestamp
                    if status["available"]:
                        rejection_time = status["rejections"].get(passenger_name)
                        if rejection_time is None or time.time() - rejection_time > 120:
                            available_drivers.append(driver)

                # If no drivers available, re-add the passenger and wait
                if not available_drivers:
                    passenger_queue.put(passenger)
                    time.sleep(2)
                    continue

                # Match passenger to the first available driver
                driver = available_drivers.pop(0)
                driver_name = driver["name"]
                distance = calculate_distance(
                    passenger["lat"], passenger["lon"], driver["lat"], driver["lon"]
                )

                driver_socket = driver["socket"]
                passenger_socket = passenger["socket"]

                # Send ride request to driver
                driver_response = send_and_receive(
                    driver_socket,
                    f"Ride request from {passenger_name}. Pickup at ({passenger['lat']}, {passenger['lon']}). Approve? (yes/no): "
                )

                if driver_response.lower() == "yes":
                    # Update availability status
                    driver_status[driver_name]["available"] = False

                    passenger_socket.send(f"Driver {driver_name} is on the way!".encode('utf-8'))
                    driver_socket.send(f"You have been assigned to passenger {passenger_name}".encode('utf-8'))
                else:
                    # Record rejection timestamp for this passenger
                    driver_status[driver_name]["rejections"][passenger_name] = time.time()

                    # Re-add the passenger to the queue
                    passenger_queue.put(passenger)

                    # Re-add the driver to the queue (still available for other passengers)
                    driver_queue.put(driver)

        except Exception as e:
            print(f"Error in worker process: {e}")

        time.sleep(0.5)


# Helper function to calculate the distance
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Helper function to send and receive messages
def send_and_receive(client_socket, message):
    try:
        client_socket.send(message.encode('utf-8'))
        return client_socket.recv(1024).decode('utf-8').strip()
    except (BrokenPipeError, ConnectionResetError) as e:
        print(f"Error sending/receiving data: {e}")
        return None  
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
    
# Handle passenger interactions
def handle_passenger(client_socket, addr, user):
    try:
        name = user["username"]
        lat = float(send_and_receive(client_socket, "Enter your pickup latitude:"))
        lon = float(send_and_receive(client_socket, "Enter your pickup longitude:"))
        passenger = {"name": name, "lat": lat, "lon": lon, "socket": client_socket}
        passenger_queue.put(passenger)
        client_socket.send("You have been added to the queue. Waiting for a driver.".encode('utf-8'))
    except Exception as e:
        print(f"Error while handling passenger {addr}: {e}")

# Handle driver interactions
def handle_driver(client_socket, addr, user):
    try:
        name = user["username"]
        lat = float(send_and_receive(client_socket, "Enter your current latitude:"))
        lon = float(send_and_receive(client_socket, "Enter your current longitude:"))
        driver = {"name": name, "lat": lat, "lon": lon, "socket": client_socket}
        driver_queue.put(driver)
        print(driver)
        client_socket.send("You are now available for ride requests.".encode('utf-8'))
    except Exception as e:
        print(f"Error while handling driver {addr}: {e}")

# Authentication handler (login and register)
def handle_authenticate(client_socket, addr):
    try:
        while True:
            client_socket.send("Do you want to login or register? (login/register): ".encode('utf-8'))
            choice = client_socket.recv(1024).decode('utf-8')

            if choice == 'login':
                client_socket.send("Enter username: ".encode('utf-8'))
                username = client_socket.recv(1024).decode('utf-8')

                client_socket.send("Enter password: ".encode('utf-8'))
                password = client_socket.recv(1024).decode('utf-8')

                # Authentication logic
                if username in user_db and user_db[username]['password'] == password:
                    role = user_db[username]['role']
                    client_socket.send(role.encode('utf-8'))
                    return user_db[username]  # Return user after success
                else:
                    client_socket.send("Invalid credentials. Try again.".encode('utf-8'))

            elif choice == 'register':
                client_socket.send("Enter username: ".encode('utf-8'))
                username = client_socket.recv(1024).decode('utf-8')

                if username in user_db:
                    client_socket.send("Username already exists. Try again.".encode('utf-8'))
                    continue

                client_socket.send("Enter password: ".encode('utf-8'))
                password = client_socket.recv(1024).decode('utf-8')

                client_socket.send("Select your role (driver or passenger): ".encode('utf-8'))
                role = client_socket.recv(1024).decode('utf-8')

                user_db[username] = {'password': password, 'role': role, "username": username}
                client_socket.send(role.encode('utf-8'))  # Send the role after registration
                return user_db[username]  # Return user data after registration

            else:
                client_socket.send("Invalid choice. Try again.".encode('utf-8'))

    except Exception as e:
        print(f"Error during authentication with {addr}: {e}")
    finally:
        pass

def handle_client(client_socket, addr):
    try:
        user = handle_authenticate(client_socket, addr)  # This is where the role/user is returned
        if user is not None:
            print(f"User authenticated: {user['username']} with role {user['role']}")
            if (user['role'] == "driver"):
                handle_driver(client_socket, addr, user)
            elif (user['role'] == "passenger"):
                handle_passenger(client_socket, addr, user)
        else:
            print("Authentication failed")
    except Exception as e:
        print(f"Unexpected error: {e}")


# Start the server
def start_server(host=host, port=port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server started at {host}:{port}")

    # Start worker processes for handling ride matching
    for _ in range(2):
        Process(target=worker_process, args=(passenger_queue, driver_queue)).start()

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        client_thread = Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()

if __name__ == "__main__":
    start_server()
