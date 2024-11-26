import socket
from math import radians, sin, cos, sqrt, atan2
from threading import Thread
import os
from dotenv import load_dotenv

load_dotenv()

passengers = {}
drivers = {}

host = os.getenv('HOST')
port = int(os.getenv('PORT'))

# Calculate distance using the Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth's radius in km

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

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

        # Add passenger details to the global dictionary
        passengers[addr] = {"name": name, "lat": lat, "long": lon}

        matched_driver_id = None

        # Find the nearest available driver
        for driver_id, driver in drivers.items():
            if driver["available"] and driver["lat"] is not None and driver["long"] is not None:
                distance = calculate_distance(lat, lon, driver["lat"], driver["long"])
                if distance < float('inf'):  # Prioritize nearest driver
                    # Connect to driver
                    driver_socket = driver.get("socket")
                    if driver_socket:
                        # Send ride request details to driver
                        response = send_and_receive(
                            driver_socket,
                            f"Ride request from {name}. Pickup at ({lat}, {lon}). Approve? (yes/no): "
                        )

                        if response.lower() == "yes":
                            matched_driver_id = driver_id
                            break

        # Inform passenger of the result
        if matched_driver_id:
            client_socket.send(
                f"Driver {drivers[matched_driver_id]['name']} is on the way!".encode('utf-8')
            )
            drivers[matched_driver_id]["available"] = False
        else:
            client_socket.send("No drivers available or approved the request. Please try again later.".encode('utf-8'))

    except Exception as e:
        print(f"Error while handling passenger {addr}: {e}")
    finally:
        client_socket.close()

# Handle driver interactions
def handle_driver(client_socket, addr):
    try:
        # Gather driver details
        name = send_and_receive(client_socket, "Enter your name: ")
        lat = float(send_and_receive(client_socket, "Enter your current latitude: "))
        lon = float(send_and_receive(client_socket, "Enter your current longitude: "))

        # Add driver details to the global dictionary
        driver_id = len(drivers) + 1
        drivers[driver_id] = {"name": name, "lat": lat, "long": lon, "available": True, "socket": client_socket}

        client_socket.send("You are now available for ride requests.".encode('utf-8'))
    except Exception as e:
        print(f"Error while handling driver {addr}: {e}")
    finally:
        # Keep driver socket open for ride requests
        pass

def handle_client(client_socket, addr):
    client_type = send_and_receive(client_socket, "Are you a driver or passenger? (Enter driver/passenger): ")

    if client_type.lower() == "driver":
        handle_driver(client_socket, addr)
    elif client_type.lower() == "passenger":
        handle_passenger(client_socket, addr)
    else:
        client_socket.send("Invalid type. Disconnecting.".encode('utf-8'))
        client_socket.close()

def start_server(host=host, port=port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)

    print(f"Server started at {host}:{port}")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")

        # Handle each client in a new thread
        client_thread = Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()

if __name__ == "__main__":
    start_server()
