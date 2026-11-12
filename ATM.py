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
print(land)
lons, lats = np.meshgrid(lons, lats)
print(np.shape(lons))
surface_indices = np.minimum(topo[1:,1:].astype(int),1023)
lon_indices, lat_indices = np.meshgrid(np.arange(1023), np.arange(1023), indexing='ij')

point1 = (120.96719977047756,23.964438421216176)
point2 = (121.17925043037455, 24.099677936693542)

fig = plt.figure(figsize=(12, 10))
ax = plt.axes(projection=ccrs.PlateCarree())


levels = np.linspace(0,60,25)
colors = ['#ffffff', '#005dff', '#0080ff', '#00a4ff', '#00c8ff', '#06edf1', '#23ffd4', '#40ffb7', '#60ff97',
'#7dff7a', '#9aff5d', '#b7ff40', '#d4ff23', '#f1fc06', '#ffdb00', '#ffb900', '#ff9400', '#ff7300',
'#ff5200', '#ff3000', '#fa0f00', '#d10000', '#a80000', '#800000']
# Create a custom colormap and normalization based on the levels
cmap = ListedColormap(colors)
norm = BoundaryNorm(levels, ncolors=cmap.N, clip=True)
level = [500,1000,1500,2000,2500]
ax.contourf(lons[1:,1:], lats[1:,1:], height[1:,1:], levels=level, cmap='binary',alpha=0.8, transform=ccrs.PlateCarree())

nox_plot = ax.contourf(lons, lats, np.zeros_like(topo),extend='max', levels = levels,cmap=cmap,norm=norm, transform=ccrs.PlateCarree())
quiver = ax.quiver(lons, lats, np.zeros_like(topo), np.zeros_like(topo),transform=ccrs.PlateCarree(), scale=110)
plt.colorbar(nox_plot, ax=ax, label=r'Nox (ppb)')
def update(frame):
    # Load dynamic data for this frame
    wind_file = f'EMISAT20150220/archive/EMISAT20150220.L.Dynamic-000{frame:03d}.nc'
    ther_file = f'EMISAT20150220/archive/EMISAT20150220.L.Tracer-000{frame:03d}.nc'

    with nc.Dataset(wind_file) as wind, nc.Dataset(ther_file) as ther:
        u = wind.variables['u'][0, :, :,:]
        v = wind.variables['v'][0, :, :,:]
        no = ther.variables['NO'][0, :, :,:]
        no2 = ther.variables['NO2'][0, :,:,:]
        no = 0.5 * (no[:, :-1, :-1] + no[:, 1:, 1:])
        no2 = 0.5 * (no2[:, :-1, :-1] + no2[:, 1:, 1:])
        print(np.shape(no2))
        u = u[surface_indices, lon_indices, lat_indices]
        v = v[surface_indices, lon_indices, lat_indices]
        nox = no+no2
        nox = nox[surface_indices, lon_indices, lat_indices]

        # Plot the interpolated surface map
        ax.clear()
        # Apply topography mask to wind data and plot quiver
        step = 10
        # Update title with time step
#point1 = 23.9239137357458, 120.89910924109085
#point2 = 24.162174671547668, 121.22235855801357
        ax.set_extent([120.89, 121.22, 23.92, 24.116], crs=ccrs.PlateCarree())
        ax.set_title(f'2015/02/20 at {frame:03d}')
        ax.add_feature(cfeature.LAND, facecolor='none')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        gl = ax.gridlines(draw_labels=True, color='gray', linestyle='--', linewidth=0.1)
        gl.top_labels = False
        gl.right_labels = False
        gl.xlabel_style = {'size': 10}
        gl.ylabel_style = {'size': 10}
        nox_plot = ax.contourf(lons[1:,1:], lats[1:,1:], nox, levels = levels, extend='max', cmap=cmap,norm=norm, transform=ccrs.PlateCarree())
        level = [500,1000,1500,2000,2500]
        ax.contourf(lons[1:,1:], lats[1:,1:], height[1:,1:], levels=level, cmap='binary', alpha=0.7,transform=ccrs.PlateCarree())
        quiver = ax.quiver(lons[::step, ::step], lats[::step, ::step], u[::step, ::step], v[::step, ::step],  transform=ccrs.PlateCarree(), scale=110)
        ax.scatter(point1[0], point1[1], color='red', s=50,  transform=ccrs.PlateCarree())
        ax.scatter(point2[0], point2[1], color='red', s=50, transform=ccrs.PlateCarree())
    return nox_plot, quiver
# Create and save the animation

anim = animation.FuncAnimation(fig, update, frames=np.arange(0,145,6), interval=200)
anim.save('atm/atm-1.gif',writer=animation.PillowWriter(fps=100))
plt.close()
