# Dockerfile with user-service installed
#
# Build with:
#   - docker build -t user-service:latest ./
#
# Run with (for local test you may have to change the port mapping:
#   - docker run -d --name ms-user-service -p 80:80 user-service
#
# Stop container with:
#   - docker stop ms-user-service
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

LABEL Author="Pol Canelles"
LABEL E-mail="canellestudi@gmail.com"
LABEL version="1.0"

# First we install/upgrade the dependencies from requirements.txt
WORKDIR /tmp
COPY requirements.txt /tmp
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy in everything else:
WORKDIR /app
COPY . /app/
