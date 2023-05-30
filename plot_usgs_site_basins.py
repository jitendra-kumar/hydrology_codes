# Query USGS server and get basic info for USGS site
def get_info_USGSsite(sitecode):
    from pygeohydro import NWIS
 
    query = {
        "site": "%s"%(sitecode)
    }
    info = NWIS().get_info(query)
    return info

# Query USGS server and get upstream contributing area for USGS site
def get_UpstreamBasin_USGSsite(sitecode):
    from pynhd import NLDI
        
    basin = NLDI().get_basins([sitecode])
    basin = basin.to_crs('EPSG:4326')
    return basin

def plot_basins(basins, basins_info, neighbor_huc12):
    """ Function to plot USGS sites, upstream basins and neighboring HUC12s
    
    Parameters
    ----------
    basins: Geometry of upstream basin 
    basins_info: Metadata information for USGS site
    neighbor_huc12: Geometries of all HUC12 within the extent/neighborhood of the upstream basin.	
    
     Return
    ------
    No returns. Make 2 subplots, first showing CONUS scale map with the
    USGS gauge sites and basins for spatial context, and second panel
    zoomed in to show the USGS gauge site, upstream basin, and
    neighboring HUC12s. 	
    """

    import matplotlib.pyplot as plt
    import contextily as cx
    from shapely.geometry import Point
    import geopandas as gpd
    
    fig, ax = plt.subplots(1,2, figsize=(20,10))
    
    # Add a CONUS plot with the subbasins
    us_states=get_US_States(48)
    us_states.boundary.plot(edgecolor='black', linewidth=1, ax=ax[0], color=None)
    neighbor_huc12.boundary.plot(edgecolor='yellow', linewidth=1, ax=ax[0], color=None)
    basins.plot(ax=ax[0], color='red')
    cx.add_basemap(ax[0], crs=basins.crs)
    
    # Add a zoomed in plot for basins
    site_loc = [Point(xy) for xy in zip(basins_info.dec_long_va, basins_info.dec_lat_va)]
    site_loc_df = gpd.GeoDataFrame(geometry = site_loc)
    
    neighbor_huc12.boundary.plot(edgecolor='grey', linewidth=1, ax=ax[1], color=None)
    basins.plot(ax=ax[1], color='blue')
    site_loc_df.plot(ax=ax[1], markersize=30, color='red', marker='o', label=basins_info.site_no[0])
    cx.add_basemap(ax[1], crs=basins.crs)
    ax[1].set_title(basins_info.station_nm[0])
    plt.tight_layout()
    plt.savefig('map_basins_%s.png'%(basins_info.site_no[0]), bbox_inches='tight', dpi=300)
    plt.show()
    
def get_US_States(nstates=48):
    """ Function to get geometry of US States from GeoJSON file.
    
	Parameters
	----------
    nstates: Number of states desired [48 (for CONUS onlY) or 50 (for all states)]

	Returns
	-------
    states: Geometry of 48 or 50 states in USA

    """
    import geopandas as gpd
    
    if (nstates not in [48, 50]):
        print("Number of US states must be 48 or 50")
        exit(1)
    
    #read US States():
    us_states = gpd.read_file('USA_states_epsg4326.geojson')
    #us_states = gpd.read_file('https://climatemodeling.org/~jkumar/data/vectors/USA_states_epsg4326.geojson')
    # extract CONUS only -- lower 48
    conus_states = us_states[~us_states.NAME_1.isin(['Alaska', 'Hawaii'])]
    if nstates==50:
        return us_states
    if nstates==48:
        return conus_states

def get_basins(id):
    """ Function to retrieve following information for a USGS gauge sites
    retrieved from USGS REST APIs https://waterdata.usgs.gov/
        -- basic metadata
        -- upstream contributing basin
        -- geometry of all HUC12 basins within the extent/neighborhood of the upstream basin
    
    Parameters
    ----------
    id : USGS site_code
    
    Returns
    -------
    basins: Geometry of upstream basin 
    basins_info: Metadata information for USGS site
    neighbor_huc12: Geometries of all HUC12 within the extent/neighborhood of the upstream basin.	
    
    """
    from pynhd import NLDI, NHDPlusHR
    from pygeohydro import NWIS
       
    basins_info=get_info_USGSsite(id)
    basins=get_UpstreamBasin_USGSsite(id)
    basins.to_file('basin_%s.json'%(id), driver="GeoJSON")
    
    # Get all HUC12s in the extent/neihborhood of the USGS gauge site for context
    hr = NHDPlusHR("huc12")
    neighbor_huc12 = hr.bygeom(basins.geometry[0].bounds)
    
    return basins,basins_info,neighbor_huc12

def main():
    #id="07340300"  # Cossatot River
    id="12488500"   # American River Watershed
    basins,basins_info,neighbor_huc12 = get_basins(id)
    plot_basins(basins,basins_info,neighbor_huc12)

if __name__ == '__main__':
    main()

