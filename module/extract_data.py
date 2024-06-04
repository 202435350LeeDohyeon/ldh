import pandas as pd
import osmnx as ox
import numpy as np
from numpy import random 

from datetime import datetime
from shapely.geometry import Point

from module.osrm_routing import *
from module.uam_osrm_routing import *
from module.uam_vertiport_routing import *
from module.helper import euclid_distance_cal
import random as rd

def dong_generator(place=None, count=100, road_type=[2,3]):

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

        geometry_inf = list(map(lambda data: [data[1],data[0]] ,geometry_inf))
        geometry_inf = Point(geometry_inf)
        # geometry_inf = [Point(coord[1], coord[0]) for coord in geometry_inf]
    # geometry_inf = list(map(lambda data: Point(data), geometry_inf))
    # geometry_inf = pd.DataFrame(geometry_inf, columns=['geometry'])
    return geometry_inf

def get_OD_data(vertiport, num = 40) :
    random_pairs = []

    for _ in range(num):
        neighborhood1, neighborhood2 = rd.sample(vertiport.keys(), 2)
        start_point = vertiport[neighborhood1]
        end_point = vertiport[neighborhood2]
        random_pairs.append([start_point, end_point])

    OD_data = []

    for i, (start_point, end_point) in enumerate(random_pairs, 1):
        OD_data.append({
            "P_O": list(vertiport.keys())[list(vertiport.values()).index(start_point)],
            "U_O": Point(start_point),
            "P_D": list(vertiport.keys() )[list(vertiport.values()).index(end_point)],
            "U_D": Point(end_point)
        })

    OD_data = pd.DataFrame(OD_data)
    ps_OV_data = pd.DataFrame()
    ps_DV_data = pd.DataFrame()
    ps_OV_data["P_O_name"] = OD_data["P_O"]
    ps_DV_data["P_D_name"] = OD_data["P_D"]
    
    OD_data["P_O"] = OD_data["P_O"].apply(lambda x: dong_generator(place=x, count=1, road_type=[2,3]))
    OD_data["P_D"] = OD_data["P_D"].apply(lambda x: dong_generator(place=x, count=1, road_type=[2,3]))
    OD_data.to_csv('./data/geometry.csv', index=False)
    return OD_data, ps_OV_data, ps_DV_data

def get_uam_OD_data(OD_data):
    uam_OD_data = []
    for index, row in OD_data.iterrows():
        U_O = Point(row['U_O'])
        U_D = Point(row['U_D'])
        uam_OD_data.append([U_O, U_D])

    return uam_OD_data

def get_ps_OD_data(OD_data):
    ps_OO_data = []
    ps_DD_data = []
    for index, row in OD_data.iterrows():
        P_O = Point(row['P_O'])
        U_O = Point(row['U_O'])
        U_D = Point(row['U_D'])
        P_D = Point(row['P_D'])
        ps_OO_data.append([P_O, U_O])
        ps_DD_data.append([U_D, P_D])

    return ps_OO_data, ps_DD_data

def timestamp_change(ps_OO, ps_OV, uam_OD, ps_DV, ps_DD) :
    for i in range(0, len(ps_OV), 4): # 0 ,4, 8, 12.....
        data = ps_OV[i:i+4]
        index = int(i/4) # 0, 1, 2, 3 ...
        for j in range(4) :
            get_out_time = 3
            data[j]['timestamp'] =  list(np.array(data[j]['timestamp'])+ ps_OO[index]['timestamp'][-1])
            if j == 3 :
                uam_OD[index]['timestamp'] = uam_OD[index]['timestamp'] + data[j]['timestamp'][-1]
        
        ps_DV[index]['timestamp'] = ps_DV[index]['timestamp'] + uam_OD[index]['timestamp'][-1]
        ps_DD[index]['timestamp'] = ps_DD[index]['timestamp'] + ps_DV[index]['timestamp'][-1]
        ps_OO[index]['timestamp'] = list(np.array(ps_OO[index]['timestamp']) + index)
        for entry in data:
                entry['timestamp'] = [t + index for t in entry['timestamp']]
        uam_OD[index]['timestamp'] = list(uam_OD[index]['timestamp'] + index)
        ps_DV[index]['timestamp'] = list(ps_DV[index]['timestamp'] + index)
        ps_DD[index]['timestamp'] =  list (ps_DD[index]['timestamp'] + index)
    return ps_OO, ps_OV, uam_OD, ps_DV, ps_DD

def timestamp_changes(ps_OO, ps_OV, uam_OD, ps_DD) :
    for i in range(0, len(ps_OV), 4): # 0 ,4, 8, 12.....
        data = ps_OV[i:i+4]
        index = int(i/4) # 0, 1, 2, 3 ...
        for j in range(4) :
            get_out_time = 3
            data[j]['timestamp'] =  list(np.array(data[j]['timestamp'])+ ps_OO[index]['timestamp'][-1])
            if j == 3 :
                uam_OD[index]['timestamp'] = uam_OD[index]['timestamp'] + data[j]['timestamp'][-1]
        ps_DD[index]['timestamp'] = ps_DD[index]['timestamp'] + uam_OD[index]['timestamp'][-1] + get_out_time
        ps_OO[index]['timestamp'] = list(np.array(ps_OO[index]['timestamp']) + index)
        for entry in data:
                entry['timestamp'] = [t + index for t in entry['timestamp']]
        uam_OD[index]['timestamp'] = list(uam_OD[index]['timestamp'] + index)
        ps_DD[index]['timestamp'] =  list (ps_DD[index]['timestamp'] + index)
    return ps_OO, ps_OV, uam_OD, ps_DD

def extract_data(vertiport, num = 40) :
    OD_data, ps_OV_data, ps_DV_data = get_OD_data(vertiport, num)

    ps_OO_data, ps_DD_data = get_ps_OD_data(OD_data)
    uam_OD_data = get_uam_OD_data(OD_data)

    ps_OO = osrm_routing_machine_multiprocess_all(ps_OO_data)
    ps_OV = uam_vertiport_routing_machine_multiprocess(ps_OV_data)
    uam_OD = uam_routing_machine_multiprocess_all(uam_OD_data)
    ps_DV = uam_vertiport_D_routing_machine_multiprocess(ps_DV_data)
    ps_DD = osrm_routing_machine_multiprocess_all(ps_DD_data)
    
    ps_OO, ps_OV, uam_OD, ps_DV, ps_DD = timestamp_change(ps_OO, ps_OV, uam_OD, ps_DV, ps_DD)
    ps = ps_OO + ps_DD
    trip = uam_OD
    
    return ps, trip, ps_OV, ps_DV