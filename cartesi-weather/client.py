import requests
from dataclasses import dataclass
import os
import subprocess
import json


from utils import *
from pathlib import Path

import numpy as np

SERVICE_URL = os.environ.get('SERVICE_URL', '127.0.0.1:5000')
'''
    Just a wrapper around a simple API call for running inference
    Uses server response to get receipts for the transaction 
'''

def denormalize(normalized_data):
    """
    Denormalize the data using min-max denormalization.

    Args:
    - normalized_data (np.ndarray): The normalized data as a 2D NumPy array.
    
    Returns:
    - np.ndarray: The denormalized data as a 2D NumPy array.
    """
    # Define min and max values for denormalization
    min_vals = np.array([-12.5, -12.6, -139.9, 0.0, -6.3, 0.0, -1.0, -2.0, -1.0, -1.999701, -99.9, -193.9, -18.6, 979.0])
    max_vals = np.array([15.1, 37.6, 159.3, 180.0, 9.1, 13.8, 1.0, 2.0, 1.0, 2.0, 100.0, 190.4, 20.3, 1040.3])

    # Perform denormalization
    denormalized_data = normalized_data * (max_vals - min_vals) + min_vals

    return denormalized_data

def run_verifiable_inference(data: str) -> dict[str, str]:
    tx_id = requests.post(f"http://{SERVICE_URL}/forecast", data).json()["tx_id"]
    tx_info = json.loads(subprocess.check_output([f"cast tx {tx_id} --json"], shell=True))
    CONTRACT_ADDRESS="0x59b22D57D4f067708AB0c00552767405926dc768"
    DAPP_ADDRESS="0xab7528bb862fb57e8a2bcd567a2e929a0be56a5e"
    n_inputs = int(subprocess.check_output([f"cast call {CONTRACT_ADDRESS} \"getNumberOfInputs(address)\" {DAPP_ADDRESS}"], shell=True).strip().decode(), 16)

    return {"tx": tx_info, "tx_id": n_inputs - 1} 

'''
Queries the output of a model inference in the Cartesi machine
'''
def query_model_outputs(tx_id: int):
    '''
    TODO for some reason this works despite not waiting for the model output.  
    Maybe the graphql request going on in the server blocks until it gets an output?
    '''
    res = requests.get(f"http://{SERVICE_URL}/forecast/{tx_id}").json()
    if res == '[]': return None

    payload = hex2str(res["notice"]["payload"])
    '''
    The payload inside the notice comes in a weird format due to
    size limitations in encrypting the model outputs. 

    For more info, refer to the dapp's source code.
    
    The code below serves to decrypt and parse the string
    that represents the model's outputs
    '''
    hex_list = find_hex_strings(payload)
    original_out_byte_sequence: list[bytes] = []
    for i in hex_list:
        original_out_byte_sequence.append(bytes.fromhex(i))


    s: str = ''
    for bs in original_out_byte_sequence:
        s += decrypt_bytes_with_private_key(bs, Path("./client/private_key.pem"))

    # Remove the outer brackets and whitespace
    s = s.replace('[', '').replace(']', '').replace('\n', ' ')

    # Parse the string into a 1D NumPy array
    arr_1d = np.fromstring(s, dtype=float, sep=' ')

    # Reshape the 1D array into a 2D array

    arr_2d = arr_1d.reshape(-1, 14)  # assuming 9 columns in each row
    
    return arr_2d

def normalize(data):
    """
    Normalize the data using min-max normalization.

    Args:
    - data (list): The input data to normalize as a list of lists.

    Returns:
    - np.ndarray: The normalized data as a 2D NumPy array.
    """
    
    # Convert the processed data to a NumPy array with float type
    data_array = data
    
    # Define min and max values for normalization
    min_vals = np.array([-12.5, -12.6, -139.9, 0.0, -6.3, 0.0, -1.0, -2.0, -1.0, -1.999701, -99.9, -193.9, -18.6, 979.0])
    max_vals = np.array([15.1, 37.6, 159.3, 180.0, 9.1, 13.8, 1.0, 2.0, 1.0, 2.0, 100.0, 190.4, 20.3, 1040.3])

    # Perform normalization
    normalized_data = (data_array - min_vals) / (max_vals - min_vals)

    return normalized_data
