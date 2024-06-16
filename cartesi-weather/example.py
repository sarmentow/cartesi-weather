import requests
import json
import numpy as np
import gradio as gr
from os import path
import pandas as pd


from pathlib import Path
from utils import feature_engineering, get_pub_key, encrypt_np_array
from client import SERVICE_URL, run_verifiable_inference, query_model_outputs, normalize, denormalize
from heatmap import generate_files


def read_random_csv_rows(csv_file_path, seed):
    # Set the random seed
    np.random.seed(seed)
    
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_file_path, sep=';')
    
    # Drop the TIME column
    df.drop('TIME', axis=1, inplace=True)
    
    # Get the number of rows in the DataFrame
    num_rows = len(df)
    
    # Generate a random starting index for the 60 sequential rows
    start_idx = 0
    # Extract the 60 sequential rows
    random_rows = df.iloc[start_idx:start_idx + 61]
    
    # Convert the DataFrame to a 2D NumPy array
    array = random_rows.to_numpy()
    
    return array

'''
This function should be some sort of generator that yields weather data every time it is called. We send the json array as
an encrypted UTF-8 encoded string
'''
def get_sample_input() -> str:
    s = read_random_csv_rows("../dataset/ASOS1.csv", 42)
    s = feature_engineering(s)
    # Discard first row
    s = s[1:]
    s = normalize(s)

    pub_key = requests.get(f'http://{SERVICE_URL}/key').text

    # Parse the JSON response and get the public key from the JSON response

    encrypted = encrypt_np_array(s)

    data = {
        'model_x': encrypted,
        'public_key': get_pub_key(Path("./client/private_key.pem"))
    }

    return json.dumps(data)
# Sample client code for using the service
outputs = [ "Temperature",  "Precipitation",  "Wind speed", "Cos wind direction",  "Sin wind direction",  "Humidity",   "Sea pressure"]
PLUS_HOURS_OPTIONS = [i for i in range(6, 145, 6)]
PARAMETER_OPTIONS = [1, 3, 5, 6, 8, 10, 13]
name_to_number = dict(zip(outputs, range(1, 15)))


from tabulate import tabulate
def fetch_results(plus_hours, parameter, sensor_grid_size):
    titles = ["Temperature diff", "Temperature", "Precipitation diff", "Precipitation", "Wind speed diff", "Wind speed", "Cos wind ", "Cos diff", "Sin wind", "Sin diff", "Humidity", "Humidity diff", "Sea diff", "Sea-level pressure"]
    # Call the inference service and get the output
    #inf = get_sample_input()
    #tx_info = run_verifiable_inference(inf)
    #out = None
    #while type(out) == type(None):
        #out: np.ndarray = query_model_outputs(tx_info['tx_id'])
    #out = denormalize(out)

    ## CREATE HTML AND PUT IT IN heatmap.html
    map_data = generate_files(sensor_grid_size, sensor_grid_size)

    # Create a line graph of the output
    return [pd.DataFrame(map_data, columns=titles), 
            gr.HTML(f"""<html><iframe src="./file/plot-map/heatmap.html" height="600px" width="100%"></iframe></html>"""),
            gr.Markdown(blog_post_content)]

def interface():
    with open("../docs/blog-post/cartesi-weather.md", "r") as f: 
        global blog_post_content
        blog_post_content = f.read()
        
    p = str(path.abspath("./plot-map/"))
    
    with gr.Blocks() as iface:
        
        with gr.Row():
            with gr.Column():
                plus_hours = gr.Slider(minimum=6, maximum=144, step=6, label="Plus Hours")
                parameter = gr.Radio(outputs, label="Parameter")
                detail_level = gr.Slider(minimum=2, maximum=20, step=1, label="Level of detail - note that increasing this will make inference a lot slower!")
                btn = gr.Button("Submit")
                gr.Markdown(blog_post_content)
                
            with gr.Column():
                output_html = gr.HTML(f"""<html><iframe src="./file/plot-map/heatmap.html" height="600px" width="100%"></iframe></html>""")
        with gr.Row():
            with gr.Column():
                title = gr.Markdown("Sample outputs from inference (each row is a simulated IoT sensor):")
                output_text = gr.DataFrame()

        btn.click(fn=fetch_results, inputs=[plus_hours, parameter, detail_level], outputs=[output_text, output_html])
    
    iface.launch(allowed_paths=[p])

if __name__ == "__main__":
        interface()