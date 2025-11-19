import geopandas as gpd

gdf = gpd.read_file("data/raw/omf_phoenix.geojson")
print(gdf.columns)
