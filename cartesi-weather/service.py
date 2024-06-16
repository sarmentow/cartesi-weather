import json

from .utils import get_pub_key, str2hex
from pathlib import Path

from flask import Flask, request

from web3 import Web3

app = Flask(__name__)

def hex2str(hex):
    """
    Decodes a hex string into a regular string
    """
    return bytes.fromhex(hex[2:]).decode("utf-8")

def send_forecast(forecast: bytes) -> str:
    return cartesi_send_str(forecast)

# TODO use custom id
def receive_forecast(id):
    from gql import gql, Client
    from gql.transport.aiohttp import AIOHTTPTransport


    # Select your transport with a defined url endpoint
    transport = AIOHTTPTransport(url="http://localhost:8080/graphql")

    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=True)

    query_str = """query notice($noticeIndex: Int!, $inputIndex: Int!) {
        notice(noticeIndex: $noticeIndex, inputIndex: $inputIndex) {
          index
          input {
            index
          }
          payload
          proof {
            validity {
              inputIndexWithinEpoch
              outputIndexWithinInput
              outputHashesRootHash
              vouchersEpochRootHash
              noticesEpochRootHash
              machineStateHash
              outputHashInOutputHashesSiblings
              outputHashesInEpochSiblings
            }
            context
          }
        }
      }
    """

    variables = {
      "noticeIndex": 0,
      "inputIndex": int(id)
    }
    

    # Provide a GraphQL query
    query = gql(query_str)

    # Execute the query on the transport
    try:
      result = client.execute(query,  variable_values=variables)
      return json.dumps(result)
    except:
        return json.dumps("[]")


def cartesi_send_str(payload: bytes) -> str:
    '''
    A bit of a mess:
    bytes (utf-8) -> str -> decode str as utf-8 literal
    
    This is necessary because of our use of the cartesi CLI send command
    TODO interact directly with the Blockchain through foundry for greater decoupling between the Cartesi infra and ours
    '''

    # Connect to local Ethereum node
    web3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))

    if web3.is_connected(): print("Connected")

    # Load the contract ABI
    with open('./client/InputBox.json') as f:
        contract_abi = json.load(f)

    contract_address = '0x59b22D57D4f067708AB0c00552767405926dc768'

    # Initialize contract
    contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    # Parameters
    dapp_address = web3.to_checksum_address('0xab7528bb862fb57e8a2bcd567a2e929a0be56a5e')
    input_data = web3.to_bytes(hexstr=str2hex(payload.decode()))

    # Encode the function call
    tx_data = contract.functions.addInput(dapp_address, input_data).build_transaction({
        'chainId': 31337,  # Chain ID for local development (Ganache, Hardhat, etc.)
        'gas': 2000000,
        'gasPrice': web3.to_wei('20', 'gwei'),
        'nonce': web3.eth.get_transaction_count('0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266'),
    })

    private_key = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'

    # Sign the transaction
    signed_tx = web3.eth.account.sign_transaction(tx_data, private_key=private_key)

    # Send the transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

    # Wait for the transaction to be mined
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    return {"tx_id": tx_receipt["transactionHash"].hex()}

'''
Web server logic
'''

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.post("/forecast")
def post_forecast():
    return send_forecast(request.data)

@app.get("/forecast/<id>")
def get_forecast(id):
    return receive_forecast(id)

@app.get("/key")
def get_key():
    key = get_pub_key(Path("./dapp/private_key.pem"))
    return key
