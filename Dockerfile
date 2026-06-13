# specify base image
FROM python:3.12.7-slim

# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# set work directory
WORKDIR /app

# install system dependencies for OpenCV, PaddleOCR, and other libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# copy requirements first for better layer caching
COPY requirements.txt .

# install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# copy the rest of the application
COPY . .

# expose the port the app runs on
EXPOSE 5001

# run the app with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "1", "--timeout", "300  ", "run:app"]
