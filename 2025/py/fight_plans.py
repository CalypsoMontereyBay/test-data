
# imports
import geopandas
from pyproj import Geod
import re
import math
import numpy as np

from shapely.geometry import Point, box
from shapely.ops import nearest_points
from geopy.distance import geodesic

from matplotlib import pyplot as plt
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER
import cartopy.feature as cfeature
from cartopy.feature import GSHHSFeature
import cartopy.io.shapereader as shpreader



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

def closest_shoreline(my_point, coastline=None, verbose:bool=True):

    buffer_degrees = 1.0
    bbox = box(
        my_point.x - buffer_degrees,
        my_point.y - buffer_degrees,
        my_point.x + buffer_degrees,
        my_point.y + buffer_degrees
)
    if coastline is None:
        reader = shpreader.Reader(shpreader.gshhs(scale='h'))
        coastline = geopandas.GeoDataFrame(geometry=list(reader.geometries()), crs="EPSG:4326")
        coastline = coastline[coastline.intersects(bbox)]

    # Calculate distances from point to filtered coastlines
    if len(coastline) > 0:
        # For polygons (like in naturalearth_lowres)
        if 'geometry' in coastline.columns:
            coastline['distance'] = coastline.geometry.apply(
                lambda geom: geom.distance(my_point)
            )
            closest_feature = coastline.loc[coastline['distance'].idxmin()]
            closest_point_on_coastline = nearest_points(my_point, closest_feature.geometry)[1]
        
        # For linestrings (like in GSHHS high-res)
        else:
            min_distance = float('inf')
            closest_point_on_coastline = None
            
            for geom in coastline.geometry:
                dist = geom.distance(my_point)
                if dist < min_distance:
                    min_distance = dist
                    closest_point_on_coastline = nearest_points(my_point, geom)[1]
        
        if verbose:
            print(f"Closest point on coastline: {closest_point_on_coastline}")
        '''
        # Get coordinates
        closest_lon = closest_point_on_coastline.x
        closest_lat = closest_point_on_coastline.y
        
        
        # Calculate distance in kilometers
        distance_km = geodesic(
            (my_point.y, my_point.x), 
            (closest_lat, closest_lon)
        ).kilometers
        
        if verbose:
            print(f"Distance to coastline: {distance_km:.2f} km")
        
        # Create a GeoDataFrame with the closest point for visualization
        closest_point_gdf = geopandas.GeoDataFrame(
            geometry=[closest_point_on_coastline], 
            crs="EPSG:4326"
        )
        return closest_point_gdf
        '''
        return closest_point_on_coastline
    else:
        raise ValueError("No coastline found in the buffer area")

def get_destination_point(wp_start, bearing, distance_km):
    """
    Calculate a new point given a starting point, bearing and distance.
    
    Parameters:
    start_lon, start_lat: coordinates of starting point in decimal degrees
    bearing: heading in degrees (0-360, clockwise from North)
    distance_km: distance in kilometers
    
    Returns:
    (lon, lat) tuple of the destination point
    """
    start_lon, start_lat = wp_start.x, wp_start.y
    # Initialize the ellipsoid
    g = Geod(ellps='WGS84')
    
    # Convert distance to meters for the calculation
    distance_m = distance_km * 1000
    
    # Calculate the new point
    # fwd returns: longitude, latitude, back azimuth
    lon2, lat2, _ = g.fwd(start_lon, start_lat, bearing, distance_m)
    
    return Point(lon2, lat2)

def get_bearing(lat1,lon1,lat2,lon2):
    dLon = lon2 - lon1;
    y = math.sin(dLon) * math.cos(lat2);
    x = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon);
    brng = np.rad2deg(math.atan2(y, x));
    if brng < 0: brng+= 360
    return brng

def plot_flight_plan(wps, outfile:str, projection:str='platecarree',
                     closest_shore=None, lon_lim=None, lat_lim=None):

    if lon_lim is None:
        hbox = 0.25
        lon_lim = wps[0].x - hbox, wps[0].x + hbox
        lat_lim = wps[0].y - hbox, wps[0].y + hbox

    fig = plt.figure(figsize=(9,9))
    plt.clf()

    tformM = ccrs.Mollweide()
    tformP = ccrs.PlateCarree()

    if projection == 'mollweide':
        tform = tformM
    elif projection == 'platecarree':
        tform = tformP

    ax = plt.axes(projection=tform)

    # Points
    wps_gdf = geopandas.GeoDataFrame(geometry=wps, crs="EPSG:4326")
    wps_gdf.plot(ax=ax, marker='o', color='red', markersize=10, transform=tform)
    if closest_shore is not None:
        closest_point_gdf = geopandas.GeoDataFrame(geometry=[closest_shore], crs="EPSG:4326")
        closest_point_gdf.plot(ax=ax, marker='^', color='b', markersize=10, transform=tform)


    # Use the full resolution GSHHS data
    land = GSHHSFeature(scale='f', levels=[1])  # 'f' is for full resolution
    ax.add_feature(land, facecolor='lightgray')

    gl = ax.gridlines(crs=ccrs.PlateCarree(), linewidth=1, 
        color='black', alpha=0.5, linestyle=':', draw_labels=True)
    gl.xlabels_top = False
    gl.ylabels_left = True
    gl.ylabels_right=False
    gl.xlines = True
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'color': 'black'}# 'weight': 'bold'}
    gl.ylabel_style = {'color': 'black'}# 'weight': 'bold'}

    # Limits
    ax.set_xlim(lon_lim)
    ax.set_ylim(lat_lim)

    # Finish
    plt.tight_layout()
    plt.savefig(outfile, dpi=300)
    print(f"Saved {outfile}")



    #plt.show()

def flightA():
    wp1 = Point(parse_dms('-121d50m52.7s', 'W'), parse_dms('36d53m28.77s','N'))

    wps = [wp1]

    closest_point_on_coastline = closest_shoreline(wp1)
    heading_to_shore = get_bearing(wp1.y, wp1.x, closest_point_on_coastline.y, closest_point_on_coastline.x)

    first_heading = heading_to_shore - 90.
    if first_heading < 0: first_heading += 360.

    wps.append(get_destination_point(wp1, first_heading, 2.))

    # Show
    plot_flight_plan(wps, 'flightA.png', closest_shore=closest_point_on_coastline)


# Command line execution
if __name__ == '__main__':
    flightA()