# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Using --no-cache-dir to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . .

# Make port 5000 available to the world outside this container
# This is informational; the actual port mapping happens during 'docker run' or in docker-compose
EXPOSE 5000

# Define environment variable for the port (can be overridden)
ENV PORT 5000
ENV GEMINI_API_KEY "" # Will be passed in at runtime

# Command to run the application using gunicorn (a production WSGI server)
# For development, you could use: CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
# For production:
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "main:app"]
