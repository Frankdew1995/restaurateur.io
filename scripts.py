
from app import app
from pathlib import Path
import subprocess


file = str(Path(app.root_path) / 'static' / 'out' / 'info_A1.docx')

out_folder = str(Path(app.root_path) / 'static' / 'out')

LIBRE_OFFICE = r"C:\Program Files\LibreOffice\program\soffice.exe"

p = subprocess.Popen([LIBRE_OFFICE, '--headless', '--convert-to', 'pdf', '--outdir',
               out_folder, file])

print([LIBRE_OFFICE, '--convert-to', 'pdf', file])
# p.communicate()