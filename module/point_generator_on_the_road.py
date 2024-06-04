''' 
###############
# Instruction #
###############
## **Generate random point geometry Function**
- osmnx를 기반으로 도로 위에 좌표를 만드는 함수

### **option** 
- **essential option**
    - place : 원하는 타겟 지역 
        - *default : None / Data_type : string*
    - count : 갯수
        - *default : 100 / Data_type : int*
- **additional option**
    - road_type : 1(고속도로), 2(간선도로), 3(집산도로)
        - *default=[1,2,3] / data_type : list*
    - save : True or False (True:It is stored in CSV format./ False: It is returned in DataFrame format)
        - *default : False / data_type : Boolean*
    - preview : True or False ()
        - *default : False / data_type : Boolean*
'''



import pandas as pd
import itertools
import osmnx as ox
from numpy import random 
from shapely.geometry import Point
from module.helper import euclid_distance_cal

########
# Main #
########
# *조회가 안 될때, https://www.openstreetmap.org 기입하고 싶은 지역명을 먼저 확인하고 실행하세요.

def point_generator(place=None, count=100, road_type=[2,3], save=False, preview=False):

    G = ox.graph_from_place(place, network_type="drive_service", simplify=False)
    _, edges = ox.graph_to_gdfs(G)

    highway_cat_list = ['motorway', 'motorway_link', 'rest_area', 'services', 'trunk', 'trunk_link']
    mainroad_cat_list = ['primary', 'primary_link', 'secondary', 'secondary_link', 'tertiary', 'tertiary_link']
    minorroad_cat_list = list(set(edges['highway']) - set(highway_cat_list + mainroad_cat_list))
    road_type_dict = {1:highway_cat_list, 2:mainroad_cat_list, 3:minorroad_cat_list}

    target_road = list(itertools.chain(*[road_type_dict[i] for i in road_type]))
    target_edges = edges.loc[[i in target_road for i in edges['highway']]]
    target_edges = target_edges.loc[(target_edges['length'] >= 10)]    
    target_edges = target_edges.reset_index()

    # 좌표 생성
    geometry_inf = []

    for i in random.choice(range(len(target_edges)), size = count, replace = True):
        #교차로 중심에 생성되지 않게 고정 미터로 생성이 아닌 해당 링크 길이로 유동적인 미터 생성
        random_num = random.choice([0.1,0.2,0.3,0.4,0.5])
        random_meter = target_edges.iloc[i]["length"] * random_num
        #좌표 생성
        new_node = list(ox.utils_geo.interpolate_points(target_edges.iloc[i]["geometry"], euclid_distance_cal(random_meter)))
        #좌표의 처음과 끝은 노드이기 때문에 제거하고 선택
        del new_node[0], new_node[-1]
        #랜덤으로 선택한 하나의 링크에서 하나의 좌표 선택 
        idx = random.choice(len(new_node), size = 1)
        geometry_loc = new_node[idx[0]]
        geometry_inf.append(geometry_loc)


    geometry_inf = list(map(lambda data: Point(data), geometry_inf))

    geometry_inf = pd.DataFrame(geometry_inf, columns=['geometry'])
    geometry_inf['lon'] = [i.x for i in geometry_inf['geometry']]
    geometry_inf['lat'] = [i.y for i in geometry_inf['geometry']]

    if preview == True:
        geometry_preview(place, geometry_inf)
        
    if save == True:
        # geometry_inf.drop(columns=['geometry'], inplace=True)
        geometry_inf.to_csv(f'{place}_geometry.csv', index=False)
        return geometry_inf
    else:
        return geometry_inf
    
##########
# helper #
##########
def geometry_preview(place, geometry_inf):
    import folium 

    places = ox.geocode_to_gdf([place])
    places = ox.project_gdf(places)

    #lat, lon
    latitude = places.lat.values[0]; longitude = places.lon.values[0]
    #기본 지도 정의
    m = folium.Map(location=[latitude, longitude],
                zoom_start=12)

    #법정경계 표시
    folium.Choropleth(geo_data=places.geometry,
                    fill_color="white",
                    ).add_to(m)

    for _, row in geometry_inf.iterrows(): 
        folium.CircleMarker(
            [row['lat'], row['lon']],
            color = 'red',
            radius = 3
            ).add_to(m)
        
    m.save(f'{place}_preview.html')