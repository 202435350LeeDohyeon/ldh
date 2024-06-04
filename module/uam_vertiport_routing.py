import numpy as np
import math
import json 
import requests
import itertools


##############################
# Helper #
##############################
def haversine(lat1, lon1, lat2, lon2):
    km_constant = 3959* 1.609344
    lat1, lon1, lat2, lon2 = map(np.deg2rad, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1 
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    km = km_constant * c
    return km

def height(altitude1, altitude2):
    height = abs(altitude1 - altitude2)/1000
    return height

# 직선 거리 걸리는 시간
def vertiport_haversine_time(distance) :
   average_speed = 0.8 # km/h
   total_time = math.ceil((distance/average_speed*60)*100)/100 # 분
   return total_time

def vertiport_height_time(altitude1, altitude2) :
   altitude = height(altitude1, altitude2)
   average_speed = 0.7 # km/h
   total_time = math.ceil((altitude/average_speed*60)*100)/100 # 분
   return total_time 

##############################
# Extract duration, distance #
##############################
def extract_vertiport_duration_distance(total_route):
   
   distance_s = sum(list(map(lambda x, y: haversine(x[1], x[0], y[1], y[0]), total_route[0:2], total_route[1:3])))
   distance_e = sum(list(map(lambda x, y: haversine(x[1], x[0], y[1], y[0]), total_route[3:4], total_route[4:5])))
   duration_s = vertiport_haversine_time(distance_s)
   duration_e = vertiport_haversine_time(distance_e)

   distance_h = height(total_route[2][2],total_route[3][2])
   duration_h = vertiport_height_time(total_route[2][2],total_route[3][2])

   
   return distance_s, distance_h, distance_e, duration_s, duration_h, duration_e

def extract_vertiport_D_duration_distance(total_route):
    distance_h = height(total_route[0][2],total_route[1][2])
    duration_h = vertiport_height_time(total_route[0][2],total_route[1][2])
    distance = sum(list(map(lambda x, y: haversine(x[1], x[0], y[1], y[0]), total_route[1:2], total_route[2:3])))
    duration = vertiport_haversine_time(distance)
    return distance_h, distance, duration_h, duration

#################
# Extract route #
#################
# def extract_vertiport_route(P_O_name) :
   
#     with open('./data/{0}.json'.format(P_O_name), 'r') as f:
#         vertiport_loc = json.load(f)
        
#     key = list(vertiport_loc[0].keys())[0]
#     total_route = vertiport_loc[0][key]
#     return total_route

def extract_vertiport_route(file_name):
    url = f'https://raw.githubusercontent.com/HNU209/DTUMOS_UAM/main/data/{file_name}.json'
    response = requests.get(url)
    if response.status_code == 200:
        vertiport_loc = json.loads(response.text)
    else:
        print(f"Error: {response.status_code}")

    key = list(vertiport_loc[0].keys())[0]
    total_route = vertiport_loc[0][key]
    return total_route

def extract_vertiport_D_route(file_name):
    url = f'https://raw.githubusercontent.com/HNU209/DTUMOS_UAM/main/data/{file_name} 도착.json'
    response = requests.get(url)
    if response.status_code == 200:
        vertiport_loc = json.loads(response.text)
    else:
        print(f"Error: {response.status_code}")
    total_route = list(vertiport_loc[0].values())[0]
    return total_route

#####################
# Extract timestamp #
#####################
def extract_vertiport_timestamp(route, duration_s, duration_h, duration_e) :
    route = route[0:-2]
    # route_2 = total_route[2:4]
    # route_3 = total_route[3:]
    rt = np.array(route)
    rt = np.hstack([rt[:-1,:], rt[1:,:]])
    per = haversine(rt[:,1], rt[:,0], rt[:,4], rt[:,3])
    per = per / np.sum(per)
    timestamp = per * duration_s
    timestamp = list(timestamp) + [duration_h] + [duration_e]
    timestamp = np.hstack([np.array([0]),timestamp])
    timestamp = list(itertools.accumulate(timestamp)) 
    timestamp = [timestamp[i:i+2] for i in range(4)]
    return timestamp

def extract_vertiport_D_timestamp(route, duration, duration_h) :
    route = route[1:]
    rt = np.array(route)
    rt = np.hstack([rt[:-1,:], rt[1:,:]])
    per = haversine(rt[:,1], rt[:,0], rt[:,4], rt[:,3])
    per = per / np.sum(per)
    timestamp = per * duration
    timestamp = [duration_h] + list(timestamp)
    timestamp = np.hstack([np.array([0]),timestamp])
    timestamp = list(itertools.accumulate(timestamp)) 
    return timestamp

########
# MAIN #
########
def uam_vertiport_routing_machine(input_data):
    result = []
    route = []

    total_route = extract_vertiport_route(input_data)
    distance_s, distance_h, distance_e, duration_s, duration_h, duration_e = extract_vertiport_duration_distance(total_route)
    timestamp = extract_vertiport_timestamp(total_route, duration_s, duration_h, duration_e)
    
    rt = np.array(total_route)
    rt = np.hstack([rt[:-1,:], rt[1:,:]])

    for i in range(len(rt)):
        segment = [rt[i][:3].tolist(), rt[i][3:6].tolist()]
        route.append(segment)
    
    for i in range(len(route)):
        data = {
            "vendor": i,
            "path": route[i],
            "timestamp": timestamp[i],
            "duration": timestamp[i][1]-timestamp[i][0]
        }
        result.append(data)

    return result

def uam_vertiport_D_routing_machine(P_D_name) : 
    total_route = extract_vertiport_D_route(P_D_name)
    distance_h, distance, duration_h, duration = extract_vertiport_D_duration_distance(total_route)
    timestamp = extract_vertiport_D_timestamp(total_route, duration, duration_h)
    total_distance = distance + distance_h
    result = {'route': total_route, 'timestamp': timestamp, 'duration': timestamp[-1], 'distance' : total_distance}
    return result

def uam_vertiport_routing_machine_multiprocess(P_O_name_data):
   P_O_data = P_O_name_data['P_O_name'].tolist()
   result = uam_vertiport_routing_machine(P_O_data[0])
   for index, P_O_name in enumerate(P_O_data):
        if index == 0 :
            continue
        for i in range(4) :
            result.append(uam_vertiport_routing_machine(P_O_name)[i])
   return result

def uam_vertiport_D_routing_machine_multiprocess(ps_DV_data) :
    P_D_data = ps_DV_data['P_D_name'].tolist()
    results = list(map(uam_vertiport_D_routing_machine, P_D_data))
    return results
