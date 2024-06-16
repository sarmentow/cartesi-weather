# This Dockerimage is responsible for building a container that can succesfully
# run Pangu-weather inference. We use it to test the model outside the Cartesi Machine

# Use the official PyTorch image as the base image
FROM pytorch/pytorch:latest

# Set the working directory to /app
WORKDIR /app

# Install any additional dependencies required by your project
# For example, if you need to install a specific package, uncomment the line below
# RUN pip install <package_name>

# Make port 8888 available to the world outside this container
EXPOSE 8888

# Define environment variable
ENV PYTORCH_VERSION 1.9.0

RUN pip install onnx onnxruntime onnx2torch gdown

# Set the default command to start a new bash shell
CMD ["bash"]
