# library
import numpy as np
import itertools
import requests
import math
from geopy.distance import geodesic
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from module.helper import calculate_straight_distance
from module.osrm_routing import extract_route

import warnings 

warnings.filterwarnings('ignore')

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

def diagonal(altitude1, altitude2):
    height = abs(altitude1-altitude2)/1000
    distance = math.sqrt((height**2)+(height**2))
    return distance

# 직선 거리 걸리는 시간
def uam_haversine_time(distance) :
   average_speed = 50 # km/h
   total_time = math.ceil((distance/average_speed*60)*100)/100 # 분
   return total_time

def uam_height_time(altitude1, altitude2) :
   altitude = height(altitude1, altitude2)
   average_speed = 10 # km/h
   total_time = math.ceil((altitude/average_speed*60)*100)/100 # 분
   return total_time 

# 사선
def uam_diagonal_time(distance) :
    average_speed = 40 # km/h
    total_time = math.ceil((distance/average_speed*60)*100)/100
    return total_time

# 사선 경로 추가
def lonlat_pythagoras(loc1, loc2) :
    point1 = [loc1[1], loc1[0]]
    point2 = [loc2[1], loc2[0]]
    # 서울역이면 고도는 40
    if point1 == [37.55311, 126.97062] or point2 == [37.55311, 126.97062] :
        target_distance = 0.04
    else :
        target_distance = 0.09
    distance = geodesic(point1, point2).kilometers
    lat = point1[0] + (point2[0] - point1[0]) * (target_distance / distance)
    lon = point1[1] + (point2[1] - point1[1]) * (target_distance / distance)
    point = [lon,lat]
    return point

#############
# OSRM base #
#############

def uam_get_res(point):

   status = 'defined'

   session = requests.Session()
   retry = Retry(connect=3, backoff_factor=0.5)
   adapter = HTTPAdapter(max_retries=retry)
   session.mount('http://', adapter)
   session.mount('https://', adapter)

   overview = '?overview=full'
   # step = '?steps=true'
   loc = f"{point[1]},{point[0]};{point[3]},{point[2]}" # lon, lat, lon, lat
   url = "http://localhost:5000/route/v1/car/"
   # url = 'http://router.project-osrm.org/route/v1/driving/'
   r = session.get(url + loc + overview) 
   
   if r.status_code!= 200:
      
      status = 'undefined'
      
      # distance    
      distance = calculate_straight_distance(point[1], point[0], point[3], point[2]) * 1000
      
      # route
      route = [[point[0], point[1]], [point[2], point[3]]]

      # duration & timestamp
      speed_km = 50#km
      speed = (speed_km * 1000/60)      
      duration = distance/speed
      
      timestamp = [0, duration] 

      result = {'route': route, 'timestamp': timestamp, 'duration': duration, 'distance' : distance}
   
      return result, status

   res = r.json()   
   return res, status

##############################
# Extract duration, distance #
##############################
def extract_uam_duration_distance(total_route):
    
    distance_s_h = diagonal(total_route[0][2],total_route[1][2])
    distance_e_h = diagonal(total_route[-1][2],total_route[-2][2])
    duration_s_h = uam_diagonal_time(distance_s_h)
    duration_e_h = uam_diagonal_time(distance_e_h)

    distance = sum(list(map(lambda x, y: haversine(x[1], x[0],  y[1], y[0]), total_route[1:-2], total_route[2:-1])))
    duration = uam_haversine_time(distance)

    return duration_s_h, duration, duration_e_h, distance_s_h, distance, distance_e_h

def extract_duration_distance(res):
       
   duration = res['routes'][0]['duration']/60
   distance = res['routes'][0]['distance']
   
   return duration, distance

#################
# Extract route #
#################
def extract_uam_route(res) :
    route = extract_route(res)
    loc_remove_s = lonlat_pythagoras(route[0],route[1])
    loc_remove_e = lonlat_pythagoras(route[-1],route[-2])
    route.insert(1, loc_remove_s)
    route.insert(-1, loc_remove_e)
    for i in range(len(route)):
        if i == 0 or i == len(route) - 1:
            # 처음 또는 끝이 서울역 위경도면 60이 되도록 수정
            if route[i] == [126.97062, 37.55311] :
                route[i].append(60)
            else : route[i].append(10)
        else:
            route[i].append(100)

    return route

#####################
# Extract timestamp #
#####################
def extract_uam_timestamp(route, duration_s_h, duration ,duration_e_h):
    route = route[1:-1]
    rt = np.array(route)
    rt = np.hstack([rt[:-1,:], rt[1:,:]])
    per = haversine(rt[:,1], rt[:,0], rt[:,4], rt[:,3])
    per = per / np.sum(per)
    timestamp = per * duration
    timestamp = np.hstack([np.array([0]),timestamp])
    timestamp = list(itertools.accumulate(timestamp)) 
    timestamp = [number + duration_s_h for number in timestamp]
    last_time = timestamp[-1] + duration_e_h
    timestamp = list(np.hstack([np.array([0]),timestamp, last_time]))
    
    return timestamp

########
# MAIN #
########

# - input : O_point, D_point (shapely.geometry.Point type)
# - output : trip, timestamp, duration, distance
def uam_routing_machine(O, D):
   res,s = uam_get_res([O.x, O.y, D.x, D.y])
   total_route = extract_uam_route(res)
   duration_s_h, duration, duration_e_h, distance_s_h, distance, distance_e_h = extract_uam_duration_distance(total_route)
   timestamp = extract_uam_timestamp(total_route, duration_s_h, duration, duration_e_h)
   total_distance = (distance_s_h + distance + distance_e_h)*1000

   result = {'route': total_route, 'timestamp': timestamp, 'duration': timestamp[-1], 'distance' : total_distance}
      
   return result

def uam_routing_machine_multiprocess(OD):
   O, D = OD
   result = uam_routing_machine(O, D)
   return result

def uam_routing_machine_multiprocess_all(OD_data):
    results = list(map(uam_routing_machine_multiprocess, OD_data))
    return results

