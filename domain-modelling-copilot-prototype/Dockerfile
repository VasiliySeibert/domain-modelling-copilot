# Use an official Python image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy project files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000
EXPOSE 8080

# Run the Flask app
CMD ["python", "app.py"]
