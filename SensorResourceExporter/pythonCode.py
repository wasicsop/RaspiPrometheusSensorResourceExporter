from prometheus_client import start_http_server, Gauge
import random
import serial
import time
import json


# read configurator file and import all varibales
with open("exporterConfigrator.json", "r") as file:
        json_data = file.read()
data_dict = json.loads(json_data)
# sensorName and portNo will be automatically read from the json file.

# create a metric for current 
new_metric = data_dict["current_metric"]
SENSOR_CURRENT = Gauge (
    new_metric["metric_name"], 
    new_metric["metric_description"], 
    list(data_dict["metric_tags"].keys())
)

# create a metric for power
new_metric = data_dict["power_metric"]
SENSOR_POWER = Gauge (
    new_metric["metric_name"], 
    new_metric["metric_description"], 
    list(data_dict["metric_tags"].keys())
)

# create a metric for voltage 
new_metric = data_dict["voltage_metric"]
SENSOR_VOLTAGE = Gauge (
    new_metric["metric_name"], 
    new_metric["metric_description"], 
    list(data_dict["metric_tags"].keys())
)

# find the names and description of all active ports
def port_mapper(indexes):
    # Convert JSON data to Python dictionary
    ports = data_dict["portMapper"]
    # Retrieve values for the given indexes
    names = []
    descriptions = []
    for index in indexes:
        port_data = ports.get(str(index))
        if port_data:
            names.append(port_data["name"])
            descriptions.append(port_data["description"])
        else:
            names.append(None)
            descriptions.append(None)
    return names, descriptions

# Decorate function with metric.
def process_request(active_ports_data):
    """A function that exposes the information of all active ports"""
    # First, construct the active_ports_data dictionary as a dictionary of dictionaries where each port name is a key,
    # and the corresponding value is another dictionary containing the port value and description:
    active_ports_data = {}
    for name, value, description in zip(active_ports_names, active_ports_values, port_description):
        active_ports_data[name] = {'value': value, 'description': description}

    #  iterate through the active_ports_data dictionary as
    for port_name, port_data in active_ports_data.items():
        print(port_name, port_data['value'], port_data['description'])
        if port_name.endswith('A'):
            SENSOR_CURRENT.labels(
                rasPi= data_dict["metric_tags"]["rasPi"], 
                microController=data_dict["metric_tags"]["microController"], 
                sensorName=port_data['description'], 
                portNo=port_name
            ).set(port_data['value'])
        elif port_name.endswith('P'):
            SENSOR_POWER.labels(
                rasPi= data_dict["metric_tags"]["rasPi"], 
                microController=data_dict["metric_tags"]["microController"], 
                sensorName=port_data['description'], 
                portNo=port_name
            ).set(port_data['value'])
        elif port_name.endswith('e'):
            SENSOR_VOLTAGE.labels(
                rasPi= data_dict["metric_tags"]["rasPi"], 
                microController=data_dict["metric_tags"]["microController"], 
                sensorName=port_data['description'], 
                portNo=port_name
            ).set(port_data['value'])
    time.sleep(0.10)    # waiting time before next execuation



if __name__ == '__main__':
    # Start up the server to expose the metrics at port number mention below.
    start_http_server(8080)
    # port name of sensor to read data from
    ser = serial.Serial('/dev/ttyAMA0', 38400)
    try:
        while True:
            # Read one line from the serial buffer
            line = ser.readline().decode().strip()
            Z = line.split(' ')                          # Create an array of the data
            if len(Z) > 2:                               # Print it nicely
                # --------- START: PRINT ON SCREEN ---------
                mid = len(Z) // 2
                print ("----------")
                print ("Vrms: \t{:}".format(Z[:-1]))
                print ("          \t", "\t".join([f"CT{i}" for i in range(1, mid+1)]))
                print ("RealPower:\t", "\t".join(Z[1:mid+1]))
                print ("Irms     :\t", "\t".join(Z[mid+1:]))               
                # --------- END: PRINT ON SCREEN ---------
                # Refer to exporterConfigrator.json file for port and indexes numbers.
                active_ports_indexes = data_dict["activePort"]         # create a list of active port indexes
                active_ports_names, port_description = port_mapper(active_ports_indexes) # port name 
                active_ports_values  = [Z[i] for i in active_ports_indexes]
                active_ports_data = dict(zip(active_ports_names, active_ports_values))
                # active_ports_data is a dictionary where each key is a port name, and the corresponding value
                # is a dictionary containing the port value and description
                for name, description in zip(active_ports_names, port_description):
                    active_ports_data[name] = {'value': active_ports_data[name], 'description': description}

                process_request(active_ports_data)
            print ("---")

    except KeyboardInterrupt:
        ser.close()