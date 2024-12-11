#!/bin/bash

# Create directories if they don't exist
mkdir -p app/static/dist/js
mkdir -p app/static/dist/css

# Download AdminLTE files
wget https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/js/adminlte.min.js -O app/static/dist/js/adminlte.min.js
wget https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/js/adminlte.min.js.map -O app/static/dist/js/adminlte.min.js.map
wget https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/css/adminlte.min.css -O app/static/dist/css/adminlte.min.css
wget https://cdn.jsdelivr.net/npm/admin-lte@3.2/dist/css/adminlte.min.css.map -O app/static/dist/css/adminlte.min.css.map
