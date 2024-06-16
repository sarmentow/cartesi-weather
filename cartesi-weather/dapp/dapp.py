from os import environ
import re
import json
import logging
# import torch
import requests
import subprocess

from model import LSTM
import torch
import numpy as np

logging.basicConfig(level="INFO")
logger = logging.getLogger(__name__)

#rollup_server = environ["ROLLUP_HTTP_SERVER_URL"]
rollup_server = 'http://127.0.0.1:5004'
logger.info(f"HTTP rollup_server url is {rollup_server}")

def encrypt_bytes_with_public_key(bytes_obj: bytes, public_key_path: str) -> bytes:
    # Create the encrypt command
    encrypt_cmd = f"openssl pkeyutl -encrypt -pubin -inkey {public_key_path} -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256"

    # Run the command and pass the bytes object to stdin
    process = subprocess.Popen(encrypt_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, _ = process.communicate(bytes_obj)

    return output

def decrypt_bytes_with_private_key(bytes_obj: bytes, private_key_path: str) -> str:
    # Create the decrypt command
    decrypt_cmd = f"openssl pkeyutl -decrypt -inkey {private_key_path} -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256 2>/dev/null"

    # Run the command and pass the bytes object to stdin
    process = subprocess.Popen(decrypt_cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    output, _ = process.communicate(bytes_obj)

    return output.decode()

def hex2str(hex):
    """
    Decodes a hex string into a regular string
    """
    return bytes.fromhex(hex[2:]).decode("utf-8")

def str2hex(str):
    """
    Encodes a string as a hex string
    """
    return "0x" + str.encode("utf-8").hex()


def find_hex_strings(text: str) -> str:
    hex_strings = re.findall(r'[0-9a-fA-F]{1,}', text)
    return hex_strings

def decrypt_np_blob(payload_model_x: str):
    hex_list = find_hex_strings(payload_model_x)
    original_out_byte_sequence: list[bytes] = []
    for i in hex_list:
        original_out_byte_sequence.append(bytes.fromhex(i))


    s: str = ''
    for bs in original_out_byte_sequence:
        s += decrypt_bytes_with_private_key(bs, "./private_key.pem")

    # Remove the outer brackets and whitespace
    s = s.replace('[', '').replace(']', '').replace('\n', ' ')

    # Parse the string into a 1D NumPy array
    arr_1d = np.fromstring(s, dtype=float, sep=' ')

    # Reshape the 1D array into a 2D array
    arr_2d = arr_1d.reshape(-1, 14)  # assuming 9 columns in each row
    return arr_2d

def handle_advance(data):
    logger.info(f"Received advance request data")
    # You have to decode hex twice. Once to go from ethereum hex to the original hex str, and then from hex to bytes
    unhexed_hex = hex2str(data['payload'])

    received_json = json.loads(unhexed_hex)

    encrypted_in = received_json['model_x']
    decrypted = decrypt_np_blob(hex2str(encrypted_in))


    # Normalize the data
#    single_time_step_scaled = normalize(json.loads(decrypted))
    single_time_step_scaled = decrypted


    # Convert to PyTorch tensor
    single_time_step_tensor = torch.tensor(single_time_step_scaled, dtype=torch.float32).unsqueeze(0)  # Add batch dimension
    single_time_step_tensor = single_time_step_tensor
    print(single_time_step_tensor)
    # Define and load the model
    model = LSTM(input_size=14, hidden_size=50, num_layers=1, output_size=14, prediction_horizon=24)
    model.load_state_dict(torch.load('model-2.pth', map_location=torch.device('cpu')))
    model.eval()

    output = None
    with torch.no_grad():
        output = model(single_time_step_tensor)

    if output == None: 
        logger.error(f"Inference didn't complete")
        return "accept"


    with open("./client_public_key.pem", "w") as f: f.write(received_json['public_key'])

    # Warning: gambiarra

    # We can't encrypt everything at once, so we just encrypt it piece by piece and then send a stringified list as a report
    to_send_original = str(output.numpy())

    # TODO find analytically how much overhead there is due to OAEP padding
    list_of_encrypted = []
    step = 400
    for i in range(0, len(to_send_original), step):
        encrypted_output = encrypt_bytes_with_public_key(to_send_original[i : i + step].encode('ascii'), "./client_public_key.pem")
        list_of_encrypted.append(encrypted_output.hex())

    try:
       inputPayload = str2hex(str(list_of_encrypted))
       ## Send the input payload as a notice
       response = requests.post(
           rollup_server + "/notice", json={"payload": inputPayload}
       )
       logger.info(
           f"Received notice status {response.status_code} body {response.content}"
       )
    except Exception as e:
        logger.error(e)


    return "accept"


def handle_inspect(data):
    logger.info(f"Received inspect request data {data}")
    return "accept"


handlers = {
    "advance_state": handle_advance,
    "inspect_state": handle_inspect,
}

finish = {"status": "accept"}

while True:
    logger.info("Sending finish")
    response = requests.post(rollup_server + "/finish", json=finish)
    logger.info(f"Received finish status {response.status_code}")
    if response.status_code == 202:
        logger.info("No pending rollup request, trying again")
    else:
        rollup_request = response.json()
        data = rollup_request["data"]
        handler = handlers[rollup_request["request_type"]]
        finish["status"] = handler(rollup_request["data"])


