#!/bin/bash

# Create directories if they don't exist
mkdir -p app/static/src/datatables/js
mkdir -p app/static/src/datatables/css
mkdir -p app/static/src/jszip
mkdir -p app/static/src/pdfmake

# DataTables Buttons JS files
wget https://cdn.datatables.net/buttons/2.4.2/js/dataTables.buttons.min.js -O app/static/src/datatables/js/dataTables.buttons.min.js
wget https://cdn.datatables.net/buttons/2.4.2/js/buttons.bootstrap5.min.js -O app/static/src/datatables/js/buttons.bootstrap5.min.js
wget https://cdn.datatables.net/buttons/2.4.2/js/buttons.html5.min.js -O app/static/src/datatables/js/buttons.html5.min.js
wget https://cdn.datatables.net/buttons/2.4.2/js/buttons.print.min.js -O app/static/src/datatables/js/buttons.print.min.js
wget https://cdn.datatables.net/buttons/2.4.2/js/buttons.colVis.min.js -O app/static/src/datatables/js/buttons.colVis.min.js

# DataTables Buttons CSS files
wget https://cdn.datatables.net/buttons/2.4.2/css/buttons.bootstrap5.min.css -O app/static/src/datatables/css/buttons.bootstrap5.min.css

# JSZip
wget https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js -O app/static/src/jszip/jszip.min.js

# PDFMake
wget https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/pdfmake.min.js -O app/static/src/pdfmake/pdfmake.min.js
wget https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.2.7/vfs_fonts.js -O app/static/src/pdfmake/vfs_fonts.js
