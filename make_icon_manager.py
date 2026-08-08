import os
import lzma
from base64 import a85encode
icons_dir = 'icons/'
out_file = 'm.py'

data = {}
for filename in os.listdir(icons_dir):
    if filename.endswith('.svg'):
        with open(os.path.join(icons_dir, filename), 'r', encoding='utf-8') as f:
            data[filename] = f.read()

data_compressed = lzma.compress(repr(data).encode('utf-8'))
data_compressed_as_str = a85encode(data_compressed).decode('utf-8')

with open(out_file, 'w', encoding='utf-8') as f:
    f.write(f'data = {repr(data_compressed_as_str)}')
