#!/bin/bash

# Install PostgreSQL development headers
apt-get update && apt-get install -y libpq-dev

# Install required packages
python3.12 -m pip install -r requirements.txt

# Run Django collectstatic
python3.12 manage.py collectstatic --noinput
