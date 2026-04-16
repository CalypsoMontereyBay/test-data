import re


def parse_dms(dms_str, direction:str):
    """
    Parse coordinates in the format "36d53m28.77s"
    Returns the decimal degree equivalent
    """
    sign = 1
    if direction in ['S', 'W']:
        sign = -1
        if direction == 'W':
            dms_str = dms_str[1:]
    # Extract degrees, minutes, and seconds using regex
    pattern = r'(\d+)d(\d+)m(\d+(?:\.\d+)?)s'
    match = re.match(pattern, dms_str)
    
    if match:
        degrees = int(match.group(1))
        minutes = int(match.group(2))
        seconds = float(match.group(3))
        
        # Convert to decimal degrees
        decimal = degrees + minutes/60 + seconds/3600
        
        # Note: This function doesn't handle negative coordinates
        # You'll need to specify direction (N/S/E/W) separately or use sign
        
        return sign*decimal
    else:
        raise ValueError(f"Could not parse DMS string: {dms_str}")
