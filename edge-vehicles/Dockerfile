# Use a lightweight Python base image
FROM python:3.8-slim

# Set the working directory inside the container
WORKDIR /app

# Copy and install dependencies first to leverage Docker caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the edge logic
COPY . .

# Set a default environment variable (will be overridden by docker-compose)
ENV VEHICLE_ID=1

# Run the orchestration script on startup
CMD ["python", "main.py"]