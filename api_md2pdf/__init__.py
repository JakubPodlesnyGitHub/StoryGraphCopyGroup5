import io
import json
import logging
import os
import tempfile
import uuid
import azure.functions as func
from contextlib import redirect_stdout

from md2pdf import md2pdf

from library.tools_validation import get_jsons_storygraph_validated, get_generic_productions_from_file, \
    print_errors_warnings


def prefix_path(path):
    func_dir = os.path.dirname(__file__)
    return os.path.join(func_dir, path)


def main(req: func.HttpRequest) -> func.HttpResponse:
    try:
        session_path = f'{tempfile.gettempdir()}/{uuid.uuid4()}'
        os.mkdir(session_path)

        pdf_path = f"{session_path}/{req.form['file_name']}"
        md2pdf(pdf_path, md_content=req.form['markdown'], css_file_path=prefix_path('pdf_styles.css'))

        with open(pdf_path, 'rb') as file_handle:
            return func.HttpResponse(file_handle.read(), mimetype="application/pdf")
    except ValueError as e:
        return func.HttpResponse(str(e), status_code=400)
