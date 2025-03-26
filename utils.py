import io
import pandas as pd
import numpy as np

# Initialize session state variables
def initialize_session_state():
    pass

# load the excel data
def load_data(uploaded_file):
    """Load uploaded Excel file into a Pandas DataFrame."""
    return pd.read_excel(uploaded_file)

# download to excel
def to_excel(dataframe):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        dataframe.to_excel(writer, index=False, sheet_name='Recommended Resources')
        writer.close()
    processed_data = output.getvalue()
    return processed_data

# Color the column
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
