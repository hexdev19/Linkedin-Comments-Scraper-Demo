import io
import csv
from typing import List, Dict, Any

def generate_csv_stream(data: List[Dict[str, Any]]) -> io.StringIO:
    output = io.StringIO()
    if not data:
        return output
    
    # Extract keys from the first dictionary
    keys = data[0].keys()
    writer = csv.DictWriter(output, fieldnames=keys)
    writer.writeheader()
    writer.writerows(data)
    
    output.seek(0)
    return output
