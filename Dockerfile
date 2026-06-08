


# specify base image
FROM python:3.12.7

# Copy the app to the work directory
WORKDIR /app

# Copy the app to the work directory
ADD . /app

# Install requirements
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

# Run the app model
CMD ["python", "run.py"]