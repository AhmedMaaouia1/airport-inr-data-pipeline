FROM python:3.10-slim

WORKDIR /opt/workdir

# System dependencies required for geospatial libraries
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libspatialindex-dev \
    libsqlite3-mod-spatialite \
    libspatialindex-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Set python path
ENV PYTHONPATH=/opt/workdir

CMD ["bash"]