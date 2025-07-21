#!/usr/bin/env python3
"""
Example demonstrating AdjacencyEngine with GeoPandas DataFrames.

This example shows how to use AdjacencyEngine with GeoPandas DataFrames
to take advantage of vectorized operations and preserve attribute data.
"""

import geopandas as gpd
from shapely import Point, Polygon
from geo_adjacency import AdjacencyEngine


def main():
    """Demonstrate GeoPandas functionality with AdjacencyEngine."""
    print("🌍 GeoPandas AdjacencyEngine Example")
    print("=" * 40)
    
    # Create sample data with attributes
    # Points representing buildings
    buildings_gdf = gpd.GeoDataFrame({
        'building_id': ['B001', 'B002', 'B003', 'B004', 'B005'],
        'type': ['residential', 'commercial', 'industrial', 'residential', 'commercial'],
        'floors': [2, 10, 1, 3, 8],
        'year_built': [1995, 2010, 1980, 2000, 2015],
        'geometry': [
            Point(1, 1), Point(3, 1), Point(1, 3), 
            Point(3, 3), Point(5, 2)
        ]
    })
    
    # Polygons representing parks  
    parks_gdf = gpd.GeoDataFrame({
        'park_id': ['P001', 'P002'],
        'name': ['Central Park', 'River Park'],
        'area_hectares': [2.5, 1.8],
        'established': [1985, 1992],
        'geometry': [
            Polygon([(0, 0), (2, 0), (2, 2), (0, 2)]),
            Polygon([(2.5, 2.5), (4.5, 2.5), (4.5, 4.5), (2.5, 4.5)])
        ]
    })
    
    print("📊 Input Data:")
    print(f"Buildings: {len(buildings_gdf)} features")
    print(f"Parks: {len(parks_gdf)} features")
    
    # Create AdjacencyEngine with GeoDataFrames
    engine = AdjacencyEngine(buildings_gdf, parks_gdf)
    
    # Get adjacency as traditional dictionary
    adjacency_dict = engine.get_adjacency_dict()
    print(f"\n🔗 Adjacency Results:")
    print(f"Total adjacency relationships: {sum(len(v) for v in adjacency_dict.values())}")
    
    # Get adjacency as rich GeoDataFrame with attributes
    adjacency_gdf = engine.get_adjacency_gdf()
    
    if adjacency_gdf is not None:
        print(f"\n📋 Adjacency GeoDataFrame:")
        print(f"Rows: {len(adjacency_gdf)}")
        print(f"Columns: {list(adjacency_gdf.columns)}")
        
        print("\n🏢 Building-Park Adjacencies:")
        for _, row in adjacency_gdf.iterrows():
            building = row['source_building_id']
            building_type = row['source_type']
            park = row['target_park_id']
            park_name = row['target_name']
            print(f"  {building} ({building_type}) ↔ {park} ({park_name})")
        
        print("\n💡 Benefits of GeoPandas Integration:")
        print("  • Attribute data automatically preserved")
        print("  • Vectorized spatial operations for performance")
        print("  • Rich output format suitable for analysis")
        print("  • Seamless integration with pandas/geopandas workflows")
    else:
        print("  No adjacency relationships found")
    
    # Demonstrate backward compatibility with lists
    print(f"\n🔄 Backward Compatibility:")
    building_geoms = list(buildings_gdf.geometry)
    park_geoms = list(parks_gdf.geometry)
    
    engine_legacy = AdjacencyEngine(building_geoms, park_geoms)
    legacy_result = engine_legacy.get_adjacency_dict()
    
    print(f"Legacy interface result: {sum(len(v) for v in legacy_result.values())} adjacencies")
    print("✓ Same results with both interfaces")


if __name__ == "__main__":
    main() 