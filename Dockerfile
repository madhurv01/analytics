# Use a specific, small, and compatible base image
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your source code into the container
COPY src/ /app/src/

# This command will be executed when the container runs
CMD ["python", "src/main.py"]