import pandas as pd
import json

def convert_string_columns(df: pd.DataFrame, threshold: float = 0.8) -> pd.DataFrame:
    """
    Converts string columns in a DataFrame to the most appropriate type 
    (int, float, datetime, bool, or valid JSON strings).
    
    Parameters:
    - df: pd.DataFrame - The input DataFrame with all columns as strings.
    - threshold: float - The minimum proportion of valid conversions required to change a column's type.
    
    Returns:
    - pd.DataFrame - The DataFrame with converted columns.
    """
    for column in df.select_dtypes(include='object').columns:
        conversion_success = {}
        
        # Attempt integer conversion
        try:
            temp = pd.to_numeric(df[column], errors='coerce', downcast='integer')
            success_rate = temp.notna().mean()
            conversion_success['integer'] = (success_rate, temp)
        except Exception:
            conversion_success['integer'] = (0, None)
        
        # Attempt float conversion
        try:
            temp = pd.to_numeric(df[column], errors='coerce', downcast='float')
            success_rate = temp.notna().mean()
            conversion_success['float'] = (success_rate, temp)
        except Exception:
            conversion_success['float'] = (0, None)
        
        # Attempt datetime conversion
        try:
            temp = pd.to_datetime(df[column], errors='coerce')
            success_rate = temp.notna().mean()
            conversion_success['datetime'] = (success_rate, temp)
        except Exception:
            conversion_success['datetime'] = (0, None)
        
        # Attempt boolean conversion
        try:
            truthy_falsy_map = {'true': True, 'false': False, '1': True, '0': False, 'yes': True, 'no': False}
            temp = df[column].str.strip().str.lower().map(truthy_falsy_map)
            success_rate = temp.notna().mean()
            conversion_success['boolean'] = (success_rate, temp.fillna(False).astype(bool))
        except Exception:
            conversion_success['boolean'] = (0, None)
        
        # Attempt JSON conversion (ensure valid JSON strings)
        try:
            def to_json_string(x):
                try:
                    x = x.replace("'", '"')  # Replace single quotes with double quotes
                    json.loads(x)  # Validate JSON structure
                    return x  # Return as a valid JSON string
                except Exception:
                    return None  # If invalid JSON, return None
            
            temp = df[column].apply(lambda x: to_json_string(x) if pd.notna(x) else None)
            success_rate = temp.notna().mean()
            conversion_success['json_string'] = (success_rate, temp)
        except Exception:
            conversion_success['json_string'] = (0, None)
        
        # Identify the best conversion based on the threshold
        best_conversion = max(conversion_success.items(), key=lambda x: x[1][0])
        if best_conversion[1][0] >= threshold:  # If success rate meets the threshold
            df[column] = best_conversion[1][1]
            print(f"Column {column} converted to {best_conversion[0]}")
        else:
            print(f"Column {column} could not be reliably converted and remains as string")
    
    return df
