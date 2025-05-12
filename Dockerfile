# Use official Python image
FROM python:3.10-slim

# Set working directory in the container
WORKDIR /app

# Copy dependency file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose port for Flask (default is 5000)
EXPOSE 5000

# Start Flask app
CMD ["python", "main.py"]
