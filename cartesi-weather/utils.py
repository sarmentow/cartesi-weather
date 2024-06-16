'''
Common utilities used across application components
'''
import subprocess
import re
import numpy as np

from pathlib import Path

def encrypt_bytes_with_public_key(bytes_obj: bytes, public_key: str) -> bytes:
    # Create the encrypt command
    encrypt_cmd = f"openssl pkeyutl -encrypt -pubin -inkey <(printf \"%s\" \"{public_key}\") -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256 2>/dev/null"

    # Run the command and pass the bytes object to stdin
    process = subprocess.Popen(encrypt_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, executable="/bin/bash")
    output, _ = process.communicate(bytes_obj)

    return output

def decrypt_bytes_with_private_key(bytes_obj: bytes, private_key_path: Path) -> str:
    # Create the decrypt command
    decrypt_cmd = f"openssl pkeyutl -decrypt -inkey {private_key_path} -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256 2>/dev/null"

    # Run the command and pass the bytes object to stdin
    process = subprocess.Popen(decrypt_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, _ = process.communicate(bytes_obj)

    return output.decode()

def get_pub_key(private_key_path: Path) -> str:
    command = f"openssl rsa -pubout -in {private_key_path} 2>/dev/null"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    output, _ = process.communicate()
    return output.decode()

def hex2str(hex: str) -> bytes:
    """
    Decodes a hex string into a regular string
    """
    return bytes.fromhex(hex[2:]).decode("utf-8")

def str2hex(s: str) -> str:
    """
    Encodes a string as a hex string
    """
    return "0x" + s.encode("utf-8").hex()

def find_hex_strings(text: str) -> str:
    hex_strings = re.findall(r'[0-9a-fA-F]{1,}', text)
    return hex_strings

def encrypt_np_array(np_array: np.ndarray) -> str:
    # Warning: gambiarra

    # We can't encrypt everything at once, so we just encrypt it piece by piece and then send a stringified list as a report
    to_send_original = str(np_array)
    # TODO find analytically how much overhead there is due to OAEP padding
    list_of_encrypted = []
    step = 400
    pub_key = get_pub_key(Path("./dapp/private_key.pem"))
    for i in range(0, len(to_send_original), step):
        # Quick hack to get encryption going with large numpy arrays
        # This shouldn't be used in production at all since it assumes the client
        # Has access to the CVM's private key. A better way would be to fetch the
        # Cartesi Machine's public key to then encrypt with it.
        encrypted_output = encrypt_bytes_with_public_key(to_send_original[i : i + step].encode('ascii'), pub_key)
        list_of_encrypted.append(encrypted_output.hex())

    return str2hex(str(list_of_encrypted))

def feature_engineering(data):
    # calculate COS and SIN columns
    wind_direction = data[:, 3]  # assume WIND DIRECTION is the 4th column
    cos_values = np.cos(np.radians(wind_direction))
    sin_values = np.sin(np.radians(wind_direction))

    wd_cos_diff = np.insert(np.diff(cos_values), 0, 0)
    wd_sin_diff = np.insert(np.diff(sin_values), 0, 0)
    temperature_diff = np.insert(np.diff(data[:, 0]), 0, 0)  # assume TEMPERATURE is the 1st column
    precipitation_diff = np.insert(np.diff(data[:, 1]), 0, 0)  # assume PRECIPITATION is the 2nd column
    wind_speed_diff = np.insert(np.diff(data[:, 2]), 0, 0)  # assume WIND SPEED is the 3rd column
    humidity_diff = np.insert(np.diff(data[:, 4]), 0, 0)  # assume HUMIDITY is the 5th column
    sea_pressure_diff = np.insert(np.diff(data[:, 5]), 0, 0)  # assume SEA-LEVEL PRESSURE is the 6th column


    temperature = data[:, 0]
    precipitation = data[:, 1]
    wind_speed = data[:, 2]
    humidity = data[:, 4]
    sea_level_pressure = data[:, 5]

    # create a new numpy array with the calculated columns
    new_data = np.zeros((data.shape[0], 14))  # -1 because of diff()
    new_data[:, 0] = temperature_diff
    new_data[:, 1] = temperature
    new_data[:, 2] = precipitation_diff
    new_data[:, 3] = precipitation
    new_data[:, 4] = wind_speed_diff
    new_data[:, 5] = wind_speed
    new_data[:, 6] = cos_values
    new_data[:, 7] = wd_cos_diff
    new_data[:, 8] = sin_values
    new_data[:, 9] = wd_sin_diff
    new_data[:, 10] = humidity
    new_data[:, 11] = humidity_diff
    new_data[:, 12] = sea_pressure_diff
    new_data[:, 13] = sea_level_pressure
    return new_data
