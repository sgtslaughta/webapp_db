# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create and set the working directory to /app
WORKDIR /app

# Copy the contents of the 'python' directory to the container at /app
COPY python/ .

# Install dependencies
RUN pip install --no-cache-dir streamlit pandas plotly.express pyyaml \
    requests mysql-connector-python

# Expose port 8088
EXPOSE 8088

# Run Connect.py when the container launches
CMD ["streamlit", "run", "New Request.py", "--browser.gatherUsageStats=false", "--server.port=8088"]
