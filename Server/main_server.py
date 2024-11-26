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

# Calculate distance using the Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

# Worker process to match passengers and drivers
def worker_process(passenger_queue, driver_queue):
    while True:
        try:
            if not passenger_queue.empty() and not driver_queue.empty():
                # Get the next passenger and driver
                passenger = passenger_queue.get()
                driver = driver_queue.get()

                # Match logic
                distance = calculate_distance(
                    passenger["lat"], passenger["lon"], driver["lat"], driver["lon"]
                )

                # Inform the passenger and driver
                driver_socket = driver["socket"]
                passenger_socket = passenger["socket"]

                # Notify driver and get confirmation
                driver_response = send_and_receive(
                    driver_socket,
                    f"Ride request from {passenger['name']}. Pickup at ({passenger['lat']}, {passenger['lon']}). Approve? (yes/no): "
                )

                if driver_response.lower() == "yes":
                    passenger_socket.send(
                        f"Driver {driver['name']} is on the way!".encode('utf-8')
                    )
                    driver_socket.send(
                        f"You have been assigned to passenger {passenger['name']}".encode('utf-8')
                    )
                else:
                    # If the driver rejects, requeue both
                    passenger_queue.put(passenger)
                    driver_queue.put(driver)

        except Exception as e:
            print(f"Error in worker process: {e}")

        time.sleep(0.5)  # Avoid busy-waiting

# Helper function to send a message and receive a response
def send_and_receive(client_socket, message):
    client_socket.send(message.encode('utf-8'))
    return client_socket.recv(1024).decode('utf-8').strip()

# Handle passenger interactions
def handle_passenger(client_socket, addr):
    try:
        # Gather passenger details
        name = send_and_receive(client_socket, "Enter your name: ")
        lat = float(send_and_receive(client_socket, "Enter your pickup latitude: "))
        lon = float(send_and_receive(client_socket, "Enter your pickup longitude: "))

        # Add passenger to the queue
        passenger = {"name": name, "lat": lat, "lon": lon, "socket": client_socket}
        passenger_queue.put(passenger)

        # Inform the passenger they are queued
        client_socket.send("You have been added to the queue. Waiting for a driver.".encode('utf-8'))
    except Exception as e:
        print(f"Error while handling passenger {addr}: {e}")
    finally:
        pass

# Handle driver interactions
def handle_driver(client_socket, addr):
    try:
        # Gather driver details
        name = send_and_receive(client_socket, "Enter your name: ")
        lat = float(send_and_receive(client_socket, "Enter your current latitude: "))
        lon = float(send_and_receive(client_socket, "Enter your current longitude: "))

        # Add driver to the queue
        driver = {"name": name, "lat": lat, "lon": lon, "socket": client_socket}
        driver_queue.put(driver)

        # Inform the driver they are available
        client_socket.send("You are now available for ride requests.".encode('utf-8'))
    except Exception as e:
        print(f"Error while handling driver {addr}: {e}")
    finally:
        pass

# Handle client connections
def handle_client(client_socket, addr):
    client_type = send_and_receive(client_socket, "Are you a driver or passenger? (Enter driver/passenger): ")

    if client_type.lower() == "driver":
        handle_driver(client_socket, addr)
    elif client_type.lower() == "passenger":
        handle_passenger(client_socket, addr)
    else:
        client_socket.send("Invalid type. Disconnecting.".encode('utf-8'))
        client_socket.close()

# Start the server
def start_server(host=host, port=port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server started at {host}:{port}")

    # Start worker processes
    for _ in range(2):  # Adjust the number of workers as needed
        Process(target=worker_process, args=(passenger_queue, driver_queue)).start()

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")

        # Handle each client in a new thread
        client_thread = Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()

if __name__ == "__main__":
    start_server()
