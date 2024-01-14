# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Make the /app inside the container if it doesn't exist
RUN mkdir -p /app

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY python/ /app

# Make port 8080 available to the world outside this container
EXPOSE 8088

# Install any needed packages specified in requirements.txt
# Uncomment the line below if you have a requirements.txt file
# COPY requirements.txt /app/
# RUN pip install --no-cache-dir -r /app/requirements.txt

# Install Streamlit and other required packages
RUN pip install streamlit pandas plotly.express pyyaml requests

# Run Connect.py when the container launches
CMD ["streamlit", "run", "/app/New Request.py",
 "--browser.gatherUsageStats=false", "--server.port=8088"]