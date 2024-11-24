import socket
import threading
from math import radians, sin, cos, sqrt, atan2

# Server configuration
HOST = 'localhost'
PORT = 12345

# Data stores
drivers = {
    1: {"name": "Driver1", "lat": 51.5074, "long": -0.1278, "available": True},
    2: {"name": "Driver2", "lat": 52.2053, "long": 0.1218, "available": True},
}
passengers = {}

# Haversine formula to calculate distance between two geographical points
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# Handle passenger requests
def handle_passenger(client_socket, addr):
    try:
        client_socket.send("Enter your name: ".encode('utf-8'))
        name = client_socket.recv(1024).decode('utf-8').strip()

        client_socket.send("Enter your pickup latitude: ".encode('utf-8'))
        lat = float(client_socket.recv(1024).decode('utf-8').strip())

        client_socket.send("Enter your pickup longitude: ".encode('utf-8'))
        lon = float(client_socket.recv(1024).decode('utf-8').strip())

        passengers[addr] = {"name": name, "lat": lat, "long": lon}

        matched_driver_id = None
        matched_driver=None
        min_distance = float('inf')
        
        for driver_id, driver in drivers.items():
            if driver["available"] and driver["lat"] is not None and driver["long"] is not None:
                distance = calculate_distance(lat, lon, driver["lat"], driver["long"])
                if distance < min_distance:
                    min_distance = distance
                    matched_driver = driver
                    matched_driver_id = driver_id  # Keep track of the matched driver's ID
        
        if matched_driver and matched_driver_id:
            client_socket.send(f"Driver {matched_driver['name']} is on the way!".encode('utf-8'))
            drivers[matched_driver_id]["available"] = False  # Update the correct driver's availability
        else:
            client_socket.send("No drivers available at the moment. Please try again later.".encode('utf-8'))

        print(drivers)
        client_socket.close()
        
    except Exception as e:
        print(f"Error while handling passenger {addr}: {e}")
        client_socket.close()



# Handle driver availability
def handle_driver(client_socket, addr):
    try:
        client_socket.send("Enter your name: ".encode('utf-8'))
        name = client_socket.recv(1024).decode('utf-8')
        driver_id = len(drivers) + 1
        drivers[driver_id] = {"name": name, "lat": None, "long": None, "available": True}
    
        client_socket.send("Enter your current latitude: ".encode('utf-8'))
        lat = float(client_socket.recv(1024).decode('utf-8'))
        client_socket.send("Enter your current longitude: ".encode('utf-8'))
        lon = float(client_socket.recv(1024).decode('utf-8'))
    
        drivers[driver_id]["lat"] = lat
        drivers[driver_id]["long"] = lon
    
        client_socket.send("You are now available for ride requests.".encode('utf-8'))
        client_socket.close()
        pass
    except Exception as e:
        print(f"Error while handling passenger {addr}: {e}")
        client_socket.close()

# Server loop
def server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print("Server started and listening on port", PORT)

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection established with {addr}")

        client_socket.send("Are you a driver or passenger? (Enter driver/passenger): ".encode('utf-8'))
        client_type = client_socket.recv(1024).decode('utf-8').lower()

        if client_type == 'passenger':
            threading.Thread(target=handle_passenger, args=(client_socket, addr)).start()
        elif client_type == 'driver':
            threading.Thread(target=handle_driver, args=(client_socket,addr)).start()
        else:
            client_socket.send("Invalid input. Disconnecting.".encode('utf-8'))
            client_socket.close()

if __name__ == "__main__":
    server()
