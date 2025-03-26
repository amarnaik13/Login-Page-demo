# utils/file_utils.py
import pandas as pd
import io
from werkzeug.utils import secure_filename
import tempfile

def load_data(uploaded_file):
    """Load uploaded Excel file into a Pandas DataFrame."""
    return pd.read_excel(uploaded_file)

def to_excel(dataframe):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='Recommended Resources')
        writer.close()
    processed_data = output.getvalue()
    return processed_data

def highlighter(val):
    color = '#ADFF2F'
    return f'background-color: {color}'

def get_name(pid, bench_data):
    bench_data["PID"] = bench_data["PID"].astype(str)
    res = bench_data[bench_data["PID"] == pid]["EE Name"]
    if not res.empty:
        res = res.values[0]
    else:
        res = "Not Available"
    return res