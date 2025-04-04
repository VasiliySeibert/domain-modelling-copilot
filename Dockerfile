# Use a base image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Set the default command
CMD ["python", "app.py"]
