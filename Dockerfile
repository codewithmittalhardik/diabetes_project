# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBUG False

# Set work directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt /code/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY . /code/

# Run collectstatic
RUN python manage.py collectstatic --noinput

# Expose port 8080
EXPOSE 8080

# Start gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "diabetes_clinical.wsgi:application"]
