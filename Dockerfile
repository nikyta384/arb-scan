# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir requests ccxt pytz

# Copy the rest of your application code into the container
COPY logs logs
COPY src src

# Command to run your application
CMD ["python3", "src/main.py"]