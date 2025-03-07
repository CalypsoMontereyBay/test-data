import pandas as pd
import simplekml
import numpy as np
import pandas

from IPython import embed

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
        line_data = df[df[flight_line_col] == line_id]
        
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

    # Do it
    #embed(header='106 of 2025/py/flight-line-kml.py')
    create_kml_from_dataframe(specim_wp, flight_folder_name='FlightA',
                              output_file='flightA.kml')