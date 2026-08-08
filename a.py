from pdf2docx import Converter
from docx import Document
import tempfile
import os

def convert(src_path:str, dest_path:str=None, password=None):
    """
    Convert a PDF file to a DOCX file.

    :param src_path: The path to the source PDF file.
    :param dest_path: The path to the destination DOCX file.
    :param password: The password for the PDF file, if it is encrypted.
    """
    src_path = os.path.abspath(src_path)
    if not os.path.exists(src_path):
        raise FileNotFoundError(f"The source file '{src_path}' does not exist.")
    if not os.access(src_path, os.R_OK):
        raise PermissionError(f"The source file '{src_path}' is not readable.")

    if dest_path is None:
        dest_path = os.path.splitext(src_path)[0] + '.docx'
    if not dest_path.endswith('.docx'):
        dest_path += '.docx'
    dest_path = os.path.abspath(dest_path)
    if os.path.exists(dest_path):
        prefix, suffix = os.path.splitext(dest_path)
        appendix = 1
        final_dest_path = f"{prefix}_{appendix}{suffix}"
        while os.path.exists(final_dest_path):
            appendix += 1
            final_dest_path = f"{prefix}_{appendix}{suffix}"
        dest_path = final_dest_path
    
    if not os.access(os.path.dirname(dest_path), os.W_OK):
        raise PermissionError(f"The destination directory '{os.path.dirname(dest_path)}' is not writable.")
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file_path = f"{temp_dir}/{os.path.basename(dest_path)}"
        cv = Converter(src_path, password=password)
        cv.convert(temp_file_path, start=0, end=None)
        cv.close()
        doc = Document(temp_file_path)
        props = doc.core_properties
        props.author=''
        props.comments=''
        doc.save(dest_path)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('src_path', type=str, help='The path to the source PDF file.')
    parser.add_argument('-o', '--output', type=str, required=False, help='The path to the destination DOCX file.')
    parser.add_argument('-p', '--password', type=str, required=False, help='The password for the PDF file, if it is encrypted.')
    args = parser.parse_args()
    convert(args.src_path, args.output, args.password)

if __name__ == '__main__':
    main()
