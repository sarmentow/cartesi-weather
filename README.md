![image](https://github.com/sarmentow/cartesi-weather/assets/48866794/f48719e6-b0f0-4c2c-bd1c-4f47bce5a8d1)

# Cartesi Weather AI weather prediction
Project built for the Cartesi Hackathon Inteli 2024 edition


## CLI fork instalation
First of all, you must install the Foundry SDK:
```
curl -L https://foundry.paradigm.xyz | bash
```

It's also important you have the docker daemon running. If you don't, **open up Docker Desktop**.

In order to run our project, you must use our fork of the Cartesi CLI (or else the container won't run) before proceeding to run the dapp inside the Cartesi Virtual Machine. 
1. Use NVM or some virtual environment to avoid conflicts with Cartesi's CLI package. Example: 
    ```
    nvm install 20.14
    nvm use 20.14
    ```
    Make sure that running `cartesi` yields an error saying `command not found`.
2. Clone the repo [sarmentow/cli](https://github.com/sarmentow/cli)
3. Install the pnpm package manager with
   ```
   curl -fsSL https://get.pnpm.io/install.sh | sh -
   ```
   (Any instalation problems with pnpm, refer to their [docs](https://pnpm.io/installation)
4. Inside the CLI directory run:
    ```
    pnpm install
    pnpm run build
    ```
5. Then, symlink the resulting executables to /usr/local/bin so that you can run it from anywhere:
    ```
    sudo ln -s $(pwd)/apps/cli/bin/run.js /usr/local/bin/cartesi
    ```
If you now type `cartesi help` you should see the cli output text in your terminal
## Installation

To setup data encryption, first generate a private key for the Cartesi Machine:
```
openssl genrsa -out cartesi-weather/dapp/private_key.pem 4096
```
You also need to generate a private key for the client so that it can decrypt the output from the Cartesi Machine model:
```
openssl genrsa -out cartesi-weather/client/private_key.pem 4096
```
Then install the packages required for the client and server applications:
```

pip install numpy==1.26.4 Flask==3.0.3 gql==3.5.0 aiohttp web3 requests gradio folium tabulate scipy

```
You can configure the url for the server application through the SERVER_URL environment variable (default address is the same as the Flask development server default 127.0.0.1:5000)


## Development setup
For better performance and faster iteration cycles, we strongly advise you to use Nonodo. In order to use it, simply run `nonodo` from any terminal session, and then, in a separate terminal, run `python3 dapp.py` from inside the `cartesi-weather/dapp` directory.

With both of these running, proceed to follow the Flask and Example instructions of the next section (ignore the part that uses the Cartesi CLI)

## Usage with the Cartesi CLI
To run the program in your machine, run the following commands in separate terminal sessions, inside the `cartesi-weather` directory:
1.  Start the API server
    ```
    flask --app service.py run
    ```
2. To run in production mode, go inside the `cartesi-weather/dapp/` directory, and build the Cartesi rollup container image:
    ```
    cartesi build

    ```
    Then, run it
    ```
    cartesi run
    ```
3. Once you have your Cartesi rollup container running, you can run inference through the `run_verifiable_inference` and `query_model_outputs` methods. For a pre-defined example you can do
    ```
    python3 example.py
    ```
You should see a message saying that the application is running. Open [http://localhost:7860/](http://localhost:7860/) in a web browser.


## More info
[Technical analysis/devlog](docs/blog-post/cartesi-weather-full.md)
