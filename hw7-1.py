import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.colors import ListedColormap,BoundaryNorm
import netCDF4 as nc
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from scipy.ndimage import gaussian_filter

land = nc.Dataset(f'TOPO.nc')
topo = land.variables['topo'][:,:]
height = land.variables['height'][:,:]*1000
mask =  land.variables['mask'][:]
lons = land.variables['lon'][:]
lats = land.variables['lat'][:]
levs =  land.variables['lev'][:]

lon_idx = np.where(np.abs(lons-120.7285)<0.01)[0][0]
lat_idx = np.where(np.abs(lats-24.1271)<0.01)[0][0]

lon_range = slice(lon_idx - 80, lon_idx + 80)
surface_indices = topo[lat_idx, lon_range].astype(int)
subset_lons = lons[lon_range]

# NOx color levels
levels = np.linspace(0, 60, 25)
colors = ['#ffffff', '#005dff', '#0080ff', '#00a4ff', '#00c8ff', '#06edf1', '#23ffd4', '#40ffb7', '#60ff97',
          '#7dff7a', '#9aff5d', '#b7ff40', '#d4ff23', '#f1fc06', '#ffdb00', '#ffb900', '#ff9400', '#ff7300',
          '#ff5200', '#ff3000', '#fa0f00', '#d10000', '#a80000', '#800000']
cmap = ListedColormap(colors)
norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)


#MW_NO = 30  # Molecular weight of NO (g/mol)
#MW_NO2 = 46  # Molecular weight of NO2 (g/mol)
#R = 8.314  # Universal gas constant (J/mol/K)
delta_z = np.diff(levs) * 1000  # Convert km to m


# Set up the figure
fig, ax = plt.subplots(3,1,figsize=(15, 10),layout='constrained',gridspec_kw={"height_ratios": [3,1,1]})
nox_plot = ax[0].pcolormesh(subset_lons, levs, np.zeros((70,160)),cmap=cmap,norm=norm)
cbar = plt.colorbar(nox_plot, ax=ax[0],location='right')
cbar.set_label("NOx Concentration (ppb)")

def update(frame):
    # Load dynamic data for the current frame
    wind_file = f'EMISAT20140107/archive/EMISAT20140107.L.Dynamic-000{frame:03d}.nc'
    chem_file = f'EMISAT20140107/archive/EMISAT20140107.L.Tracer-000{frame:03d}.nc'
    ther_file = f'EMISAT20140107/archive/EMISAT20140107.L.Thermodynamic-000{frame:03d}.nc'
    with nc.Dataset(wind_file) as wind, nc.Dataset(chem_file) as chem, nc.Dataset(ther_file) as ther:
        u = wind.variables['u'][0, :, lat_idx-1:lat_idx+1, lon_range]
        w = wind.variables['w'][0, :, lat_idx, lon_range]
        no = chem.variables['NO'][0, :, lat_idx, lon_range]
        no2 = chem.variables['NO2'][0, :, lat_idx, lon_range]
        theta = ther.variables['th'][0, :, lat_idx, lon_range]
        # Calculate NOx at grid centers
        u = 0.5 * (u[:, :-1] + u[:, 1:])
        u = u.mean(axis=1)
        nox = no+no2
        print(np.shape(nox))
        # Mask regions below topography
        nox_masked = np.ma.masked_where(np.arange(len(levs))[:, None] < surface_indices, nox)
        u_masked = np.ma.masked_where(np.arange(len(levs))[:, None] < surface_indices, u)
        w_masked = np.ma.masked_where(np.arange(len(levs))[:, None] < surface_indices, w)
        theta_masked = np.ma.masked_where(np.arange(len(levs))[:, None] < surface_indices, theta)
        # Calculate boundary layer height for each longitude
        abl_heights = []
        for lon_idx in range(theta_masked.shape[1]):  # Loop over longitudes
            th_col = theta_masked[:, lon_idx]
            min_theta = th_col.min()
            abl_idx = np.where((th_col - min_theta)-0.5 < 0.01)[0]  # Find first index where θ > min(θ) + 0.5 K
            abl_heights.append(levs[abl_idx[-1]])

        # Calculate Vertical-Integrated NOx (mg/m²)
        air_density = 1.225  # kg/m³
        nox_mass_density = (
            nox_masked[:-1,:] * 1e-9 * air_density * delta_z[:, None] * 1e3 *1e3
        ) 
        nox_integrated = np.nansum(nox_mass_density, axis=0)  # Sum across vertical layers

        # Calculate NO2/NOx Ratio
        ratio_no2_nox = np.nanmean(no2 / nox, axis=0)

        # Clear the axis and plot NOx
        ax[0].clear()
        nox_plot = ax[0].pcolormesh(subset_lons, levs, nox_masked,cmap=cmap, norm=norm)
        # Plot wind vectors
        step = 10
        quiver = ax[0].quiver(
               subset_lons[::step],levs , 
               u[:, ::step], w[:, ::step], 
               angles='uv',
               scale=35,  # Adjust scale for arrow length (tweak this value if arrows are too short/long)
               width=0.002
        )
        ax[0].quiverkey(
               quiver,  # The quiver object
               X=0.95, Y=1.03,  # Position of the key in figure coordinates (X, Y are relative to the axes)
               U=1,  # Arrow length representing the value (adjust as needed)
               label="1 m/s",  # Label for the quiver key
               labelpos="E",  # Position of the label relative to the arrow ('N', 'E', 'S', 'W')
               coordinates="axes",  # Use axes coordinates for placement
        )
        abl = ax[0].plot(subset_lons, abl_heights, color='green', label='Boundary Layer (θ + 0.5 K)')
        # Plot topography
        ax[0].fill_between(subset_lons, levs[surface_indices], levs[0], color='gray')
        ax[0].set_ylim([0,3])
        # Labels and formatting
        ax[0].set_xlabel("Longitude")
        ax[0].set_ylabel("Height (km)")
        ax[0].set_title(f"Taiping, Taichung City 2019/01/07 at {frame}")
        ax[0].legend()

        ax[1].clear()
        no1 = ax[1].plot(subset_lons, nox_integrated, label='Vertical-Integrated NOx (mg/m²)', color='blue')
        ax[1].set_ylabel("(mg/m²)")
        ax[1].set_ylim([0,70])
        ax[1].legend()
        ax[1].grid()

        ax[2].clear()
        no2 = ax[2].plot(subset_lons, ratio_no2_nox, label='NO2/NOx Ratio', color='red')
        ax[2].set_xlabel("Longitude")
        ax[2].set_ylabel("ratio")
        ax[2].set_ylim([0.5,1.5])
        ax[2].legend()
        ax[2].grid()

    return nox_plot, quiver, abl, no1, no2

# Create the animation
anim = animation.FuncAnimation(fig, update, frames=np.arange(0, 145,6), interval=200)
anim.save('hw7/hw7-1.gif', writer=animation.PillowWriter(fps=10))
plt.close()
