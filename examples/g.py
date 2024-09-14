from pycomm.ab_comm.clx import Driver as ClxDriver
import logging
from time import sleep
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin
import json
import subprocess
import platform

app = Flask(__name__)
CORS(app)

# Create a ClxDriver instance
c = ClxDriver()
is_connected = False  # Flag to track connection status

@app.route('/insertDataToPlc', methods=['POST'])
@cross_origin()
def insert_data_to_plc():
    global is_connected  # Access the global flag

    try:
        if not is_connected:  # Check if connection needs to be established
            c.open('10.60.85.21')  # Open connection to the PLC (only once)
            print("Connection to PLC established.")
            is_connected = True

        c.forward_open()  # Initialize the session

        # Get the JSON data from the request
        data_list = request.json

        # Iterate through the data and process it
        for item in data_list:
            for key, value in item.items():
                # Convert value to string regardless of its type
                str_value = str(value)
                
                print("Writing to PLC: Key:", type(key), "Value:", type(str_value))
                
                # Write string value to PLC
                key = key.encode('utf-8')
                str_value = str_value.encode('utf-8')
                try:
                    c.write_string(key, str_value)
                    print("Read String Value is", c.read_string(key))
                    print("Data written to PLC successfully for key:", key.decode('utf-8'))
                except Exception as e:
                    print("Error writing string:", key.decode('utf-8'), ":", e)
                sleep(1)

        return jsonify({"message": "Data written to PLC successfully.", "error": None}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({"message": "Error occurred while writing data to PLC.", "error": str(e)}), 500
    finally:
        if is_connected:
            c.close()
            is_connected = False
            print("Connection to PLC closed.")

@app.route('/closeConnection', methods=['GET'])
def close_connection():
    global is_connected
    if is_connected:
        c.close()
        is_connected = False
        print("Connection to PLC closed.")
    return jsonify({"message": "Connection to PLC closed successfully.", "error": None}), 200

# Add the ping route
@app.route('/ping', methods=['GET'])
def ping():
    ip_address = request.args.get('ip')
    
    if not ip_address:
        return jsonify({"message": "No IP address provided.", "error": None}), 400

    try:
        # Platform-specific command
        if platform.system().lower() == "windows":
            command = ['ping', '-n', '1', ip_address]
        else:
            command = ['ping', '-c', '1', ip_address]

        # Execute the ping command
        response = subprocess.call(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if response == 0:
            return jsonify({"ip": ip_address, "reachable": True}), 200
        else:
            return jsonify({"ip": ip_address, "reachable": False}), 200
    except Exception as e:
        print("Ping error:", e)
        return jsonify({"message": "Error occurred during ping.", "error": str(e)}), 500
    
# Add the ping_wifi route
@app.route('/pingWifi', methods=['GET'])
def ping_wifi():
    wifi_ip_address = request.args.get('wifi_ip_address')
    
    if not wifi_ip_address:
        return jsonify({"message": "No Wi-Fi IP address provided.", "error": None}), 400

    try:
        # Platform-specific command for pinging
        if platform.system().lower() == "windows":
            command = ['ping', '-n', '1', wifi_ip_address]
        else:
            command = ['ping', '-c', '1', wifi_ip_address]

        # Execute the ping command
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        # Convert stdout to string for easier searching
        stdout_str = stdout.decode('utf-8').lower()
        
        # Log the output for debugging
        print("Ping command output:", stdout_str)
        print("Ping command error:", stderr.decode('utf-8'))

        # Check for "Destination host unreachable"
        if "destination host unreachable" in stdout_str:
            return jsonify({"ip": wifi_ip_address, "reachable": False, "message": "Internet connection is not active."}), 200
        elif process.returncode == 0:
            return jsonify({"ip": wifi_ip_address, "reachable": True}), 200
        else:
            return jsonify({"ip": wifi_ip_address, "reachable": False}), 200
    except Exception as e:
        # Log the exception for debugging
        print("Ping error (Wi-Fi):", str(e))
        return jsonify({"message": "Error occurred during Wi-Fi ping.", "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8083)
