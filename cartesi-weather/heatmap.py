import numpy as np
import random
import folium
from folium.plugins import HeatMap
from scipy.interpolate import griddata
import os

import json
import requests

import sys

from pathlib import Path
from utils import encrypt_np_array, get_pub_key, feature_engineering
from client import SERVICE_URL, run_verifiable_inference, query_model_outputs

# Function to generate the 10x10 sensor mesh
def generate_sensor_mesh(i, j):
    start_lat = 35.5537
    start_lon = 129.2381 

    # Calculate grid spacing (100 meters)
    spacing = 0.01  # 0.001 degree ≈ 100 meters

    # Generate sensor coordinates
    lats = np.linspace(start_lat, start_lat + spacing * (i - 1), i)
    lons = np.linspace(start_lon, start_lon + spacing * (j - 1), j)

    # Create a meshgrid of coordinates
    grid_lats, grid_lons = np.meshgrid(lats, lons)

    # Flatten the meshgrid into individual latitude and longitude points
    sensor_lats = grid_lats.flatten()
    sensor_lons = grid_lons.flatten()
    
    return sensor_lats, sensor_lons

# Function to generate random weather data for each parameter
def generate_random_weather_data(size):
    weather_data = [[
        [
            round(random.uniform(25, 33), 1),  # Random temperature between 25 and 33 degrees Celsius
            round(random.uniform(0, 50), 1),  # Random precipitation between 0 and 50 mm
            round(random.uniform(0, 20), 1),  # Random wind speed between 0 and 20 m/s
            random.randint(0, 360),  # Random wind direction between 0 and 360 degrees
            random.randint(0, 100),  # Random humidity between 0 and 100 percent
            round(random.uniform(950, 1050), 1),  # Random sea-level pressure between 950 and 1050 hPa
        ]
        for _ in range(60)
    ] for _ in range(size) 
    ]
    
    return weather_data

def get_sample_inputs(data_e) -> str:

    pub_key = requests.get(f'http://{SERVICE_URL}/key').text

    # Parse the JSON response and get the public key from the JSON response
    data_e = feature_engineering(data_e)
    encrypted = encrypt_np_array(data_e)

    data = {
        'model_x': encrypted,
        'public_key': get_pub_key(Path("./client/private_key.pem"))
    }

    return json.dumps(data)

# Function to generate a Folium map for each parameter
def generate_maps(parameter_data, sensor_lats, sensor_lons):
    maps = {}
    
    for idx in range(14):
        parameter_value = []
        for values in parameter_data:
            parameter_value.append(values[idx])  # Get the ith element of values array
        
        # Interpolate parameter values onto the sensor mesh
        grid_x, grid_y = np.meshgrid(sensor_lats, sensor_lons)
        grid_values = np.array(parameter_value)
            
        # Check if dimensions match
        if len(grid_values) != len(sensor_lats):
            raise ValueError(f"Number of values ({len(grid_values)}) does not match number of points ({len(sensor_lats)})")
        
        # Create a Folium map centered on the mean latitude and longitude of the sensor mesh
        map_center = [np.mean(sensor_lats), np.mean(sensor_lons)]
        mymap = folium.Map(location=map_center, zoom_start=10)

        # Perform interpolation of parameter values on the grid
        grid_z = griddata((sensor_lats, sensor_lons), grid_values, (grid_x, grid_y), method='linear')
        grid_z[np.isnan(grid_z)] = 0  # Replace NaN values with 0
        
        # Convert grid to list of points for HeatMap
        points = []
        for i in range(len(grid_x)):
            for j in range(len(grid_y)):
                points.append([grid_x[i, j], grid_y[i, j], grid_z[i, j]])
        
        # Add HeatMap layer to map
        HeatMap(points, radius=70, blur=70).add_to(mymap)
        
        # Add OpenStreetMap tiles
        folium.TileLayer('openstreetmap').add_to(mymap)
        
        # Example: Display parameter_value on map as a marker
        # Save the map to a dictionary with parameter name as key
        parameter_name = f'Parameter {idx + 1}'
        maps[parameter_name] = mymap
    
    return maps

def generate_files(i, j):
    # Generate sensor mesh coordinates
    sensor_lats, sensor_lons = generate_sensor_mesh(i,j)

    # Generate random weather data for each parameter
    weather_data = generate_random_weather_data(i*j)

    predictions = []
    id_list = []
    for data in weather_data:
        tx_info = run_verifiable_inference(get_sample_inputs(np.array(data)))
        tx_id = tx_info["tx_id"]
        id_list.append(tx_id)

    print("Getting responses")
    for _, idx in enumerate(id_list):
        out = None
        while type(out) == type(None):
            out: np.ndarray = query_model_outputs(idx)
        predictions.append(out)


    for idx in range(24):
        map_data = []
        for arr in predictions:
            map_data.append(arr[idx])
        # Generate maps for each parameter using the sensor mesh and weather data

        parameter_maps = generate_maps(map_data, sensor_lats, sensor_lons)
            # Save or display the generated maps (here we save each map as an HTML file)
        for parameter, mymap in parameter_maps.items():
            param_no = parameter.split(' ')[-1]
            map_filename = f'{(idx + 1) * 6}_{param_no}.html'
            os.makedirs(f"plot-map/T+{(idx + 1) * 6}", exist_ok=True)
            mymap.save(f"plot-map/T+{(idx + 1) * 6}/{map_filename}")
            #print(f"Map saved: {map_filename}")
    return map_data
