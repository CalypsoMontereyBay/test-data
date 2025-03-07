
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
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
from mpl_toolkits.axes_grid1.inset_locator import mark_inset

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

insight = Point(parse_dms('-121d50m41.22s', 'W'), parse_dms('36d54m29.35s','N'))

def plot_flight_plan(wps, outfile:str, projection:str='platecarree',
                     closest_shore=None, lon_lim=None, lat_lim=None):

    hbox_in = 0.035
    hbox_out = 0.25

    def set_lims(wp, hbox):
        lon_lim = wp.x - hbox, wp.x + hbox
        lat_lim = wp.y - hbox, wp.y + hbox
        return lon_lim, lat_lim

    tformM = ccrs.Mollweide()
    tformP = ccrs.PlateCarree()

    if projection == 'mollweide':
        tform = tformM
    elif projection == 'platecarree':
        tform = tformP


    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 8),
        subplot_kw={'projection': tform})

    # Points
    wps_gdf = geopandas.GeoDataFrame(geometry=wps, crs="EPSG:4326")
    wps_gdf.plot(ax=ax1, marker='o', color='red', markersize=10, transform=tform,
                 label='Waypoints')

    if closest_shore is not None:
        closest_point_gdf = geopandas.GeoDataFrame(geometry=[closest_shore], crs="EPSG:4326")
        closest_point_gdf.plot(ax=ax1, marker='^', color='b', markersize=10, transform=tform,
                               label='Closest shore')

    # Insight
    insight_gdf = geopandas.GeoDataFrame(geometry=[insight], crs="EPSG:4326")
    insight_gdf.plot(ax=ax1, marker='s', color='k', markersize=10, transform=tform,
                     label='Insight', zorder=10)

    # Use the full resolution GSHHS data
    land = GSHHSFeature(scale='f', levels=[1])  # 'f' is for full resolution
    ax1.add_feature(land, facecolor='lightgray')

    gl = ax1.gridlines(crs=ccrs.PlateCarree(), linewidth=1, 
        color='black', alpha=0.5, linestyle=':', draw_labels=True)
    gl.xlabels_top = False
    gl.ylabels_left = True
    gl.ylabels_right=False
    gl.xlines = True
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    gl.xlabel_style = {'color': 'black'}# 'weight': 'bold'}
    gl.ylabel_style = {'color': 'black'}# 'weight': 'bold'}

    # Zoom out
    lon_lim, lat_lim = set_lims(wps[0], hbox_out)
    ax1.set_xlim(lon_lim)
    ax1.set_ylim(lat_lim)

    # Zoom in
    wps_gdf.plot(ax=ax2, marker='o', color='red', markersize=5, transform=tform,
                 label='Waypoints')
    insight_gdf.plot(ax=ax2, marker='s', color='k', markersize=10, transform=tform,
                     label='Insight', zorder=10)
    ax2.add_feature(land, facecolor='lightgray')

    lon_lim, lat_lim = set_lims(wps[0], hbox_in)
    ax2.set_xlim(lon_lim)
    ax2.set_ylim(lat_lim)

    ax2.legend()


    # Finish
    plt.tight_layout()
    plt.savefig(outfile, dpi=300)
    print(f"Saved {outfile}")



def trunc_heading(heading):
    """
    Truncate heading to 0-360 degrees
    """
    while heading < 0:
        heading += 360
    while heading >= 360:
        heading -= 360
    return heading


def flightA(line_size=2., off_line=70e-3, plot:bool=False):

    wp1 = Point(parse_dms('-121d50m52.7s', 'W'), parse_dms('36d53m28.77s','N'))

    wps = [wp1]

    closest_point_on_coastline = closest_shoreline(wp1)
    heading_to_shore = get_bearing(wp1.y, wp1.x, closest_point_on_coastline.y, closest_point_on_coastline.x)

    along_heading = heading_to_shore - 90.
    along_heading = trunc_heading(along_heading)
    back_heading = trunc_heading(along_heading + 180)

    wps.append(get_destination_point(wp1, along_heading, 2.))

    # Next line, 70m off-shore
    off_heading = trunc_heading(heading_to_shore+180)

    wps.append(get_destination_point(wps[-1], off_heading, off_line))
    wps.append(get_destination_point(wps[-1], back_heading, line_size))

    # Next lines
    nlines = int(np.round(line_size/off_line))
    along = True
    for i in range(nlines-2):
        wps.append(get_destination_point(wps[-1], off_heading, off_line))
        if along:
            wps.append(get_destination_point(wps[-1], along_heading, line_size))
        else:
            wps.append(get_destination_point(wps[-1], back_heading, line_size))
        along = not along


    # Show
    if plot:
        plot_flight_plan(wps, 'flightA.png', closest_shore=closest_point_on_coastline)

    wps_gdf = geopandas.GeoDataFrame(geometry=wps, crs="EPSG:4326")
    # Write to file
    wps_gdf.to_file('flightA.shp')

    # Write to KML
    wps_gdf.to_file('flightA.kml', driver='KML')

    # Write to CSV as lat lon
    wps_gdf['lon'] = wps_gdf.geometry.x
    wps_gdf['lat'] = wps_gdf.geometry.y
    wps_gdf['Waypoint'] = [f'WP{i:03d}' for i in np.arange(len(wps_gdf))]
    wps_gdf[['WP', 'lon', 'lat']].to_csv('flightA.csv', index=False)


# Command line execution
if __name__ == '__main__':
    flightA(plot=False)