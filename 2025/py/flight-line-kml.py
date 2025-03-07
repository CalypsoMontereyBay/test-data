import pandas as pd
import simplekml
import numpy as np
import pandas

# Sample data - replace this with your actual DataFrame
# This example creates 3 flight lines with 5 points each
def create_sample_data():
    # Create coordinates for 3 flight lines
    np.random.seed(42)  # For reproducibility
    
    flight_lines = []
    
    # Create 3 flight lines
    for i in range(3):
        # Base coordinates - modify these to match your area of interest
        base_lat = 35.0 + (i * 0.01)
        base_lon = -118.0
        
        # Create 5 points for each flight line
        lats = [base_lat + (j * 0.005) for j in range(5)]
        lons = [base_lon + (j * 0.005) for j in range(5)]
        
        # Create a dataframe for this flight line
        line_df = pd.DataFrame({
            'flight_line': i+1,
            'latitude': lats,
            'longitude': lons,
            'point_num': range(1, 6)
        })
        
        flight_lines.append(line_df)
    
    # Combine all flight lines into one dataframe
    return pd.concat(flight_lines, ignore_index=True)

def create_kml_from_dataframe(df, output_file='flight_lines.kml', 
                              flight_line_col='flight_line', 
                              flight_folder_name='Flight Lines',
                              lat_col='latitude', 
                              lon_col='longitude'):
    """
    Create a KML file with flight lines from a pandas DataFrame.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame containing latitude, longitude, and flight line identifiers
    output_file : str
        Path to save the KML file
    flight_line_col : str
        Column name in df that identifies different flight lines
    lat_col : str
        Column name for latitude values
    lon_col : str
        Column name for longitude values
    """
    # Create a new KML object
    kml = simplekml.Kml()
    
    # Create a folder for all flight lines
    flight_folder = kml.newfolder(name=flight_folder_name)
    
    # Get unique flight lines
    flight_lines = df[flight_line_col].unique()
    
    # Create a line for each flight line
    for line_id in flight_lines:
        # Filter data for this flight line
        line_data = df[df[flight_line_col] == line_id].sort_values('point_num')
        
        # Create a new line string
        line = flight_folder.newlinestring(name=f"FL{line_id}")
        
        # Add coordinates to the line
        coords = [(row[lon_col], row[lat_col]) for _, row in line_data.iterrows()]
        line.coords = coords
        
        # Set line style - change colors if needed
        line.style.linestyle.color = simplekml.Color.blue
        line.style.linestyle.width = 3
        
        # Add start and end point markers
        start_point = flight_folder.newpoint(name=f"Start Line {line_id}")
        start_point.coords = [coords[0]]
        start_point.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle_highlight.png'
        
        end_point = flight_folder.newpoint(name=f"End Line {line_id}")
        end_point.coords = [coords[-1]]
        end_point.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'
    
    # Save the KML
    kml.save(output_file)
    print(f"KML file created: {output_file}")
    return output_file

# For demonstration purposes, create sample data
# In your real code, you would use your actual DataFrame instead
df = create_sample_data()
print("Sample DataFrame Preview:")
print(df.head())

# Create the KML file from the DataFrame
kml_file = create_kml_from_dataframe(df, output_file='flight_lines.kml')

# If your actual data has different column names, you can specify them:
# kml_file = create_kml_from_dataframe(
#     df, 
#     output_file='flight_lines.kml',
#     flight_line_col='your_flight_line_column',
#     lat_col='your_latitude_column', 
#     lon_col='your_longitude_column'
# )

def waypoint_to_df(waypoint_file:str):

    wp = pandas.read_table(
        waypoint_file, skiprows=1,
        names=['sequence', 'current_waypoint', 'coordinate_frame', 'command', 'param1', 'param2',
               'param3','param4','latitude','longitude','altitude','autocontinue'])

    # Specim only
    good_rows = np.zeros(len(wp), dtype=bool)
    for ss, row in wp.iterrows():
        # 206
        if row.command == 206:
            good_rows[ss-1] = True
            sv_last = ss-1
    # Trim the last one
    good_rows[sv_last] = False
    specim_wp = wp[good_rows].copy()

    # Return
    return specim_wp


# Command line execution
if __name__ == '__main__':
    import sys

    # Load waypoint file
    ifile = sys.argv[1]
    specim_wp = waypoint_to_df(ifile)

    # Add flight lines
    flight_lines = []
    for ss in range(len(specim_wp)//2):
        flight_lines.append(ss+1)
        flight_lines.append(ss+1)
    specim_wp['flight_line'] = flight_lines    