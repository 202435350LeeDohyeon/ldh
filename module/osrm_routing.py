# library
import numpy as np
import itertools
import requests
import polyline
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from module.helper import calculate_straight_distance


import warnings 

warnings.filterwarnings('ignore')

#############
# OSRM base #
#############
def get_res(point):

   status = 'defined'

   session = requests.Session()
   retry = Retry(connect=3, backoff_factor=0.5)
   adapter = HTTPAdapter(max_retries=retry)
   session.mount('http://', adapter)
   session.mount('https://', adapter)

   overview = '?overview=full'
   loc = f"{point[0]},{point[1]};{point[2]},{point[3]}" # lon, lat, lon, lat
   # url = "http://127.0.0.1:5000/route/v1/driving/"
   url = 'http://router.project-osrm.org/route/v1/driving/'
   r = session.get(url + loc + overview) 
   
   if r.status_code!= 200:
      
      status = 'undefined'
      
      # distance    
      distance = calculate_straight_distance(point[1], point[0], point[3], point[2]) * 1000
      
      # route
      route = [[point[0], point[1]], [point[2], point[3]]]

      # duration & timestamp
      speed_km = 10#km
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
def extract_duration_distance(res):
       
   duration = res['routes'][0]['duration']/60
   distance = res['routes'][0]['distance']
   
   return duration, distance

#################
# Extract route #
#################
def extract_route(res):
    
    route = polyline.decode(res['routes'][0]['geometry'])
    route = list(map(lambda data: [data[1],data[0]] ,route))
    
    return route

#####################
# Extract timestamp #
#####################
def extract_timestamp(route, duration):
    
    rt = np.array(route)
    rt = np.hstack([rt[:-1,:], rt[1:,:]])

    per = calculate_straight_distance(rt[:,1], rt[:,0], rt[:,3], rt[:,2])
    per = per / np.sum(per)

    timestamp = per * duration
    timestamp = np.hstack([np.array([0]),timestamp])
    timestamp = list(itertools.accumulate(timestamp)) 
    
    return timestamp
 
########
# MAIN #
########

# - input : O_point, D_point (shapely.geometry.Point type)
# - output : trip, timestamp, duration, distance
def osrm_routing_machine(O, D):
       
   osrm_base, status = get_res([O.y, O.x, D.y, D.x])
   
   if status == 'defined':
      duration, distance = extract_duration_distance(osrm_base)
      route = extract_route(osrm_base)
      timestamp = extract_timestamp(route, duration)

      result = {'route': route, 'timestamp': timestamp, 'duration': duration, 'distance' : distance}
      
      return result
   else: 
      return osrm_base

def osrm_routing_machine_multiprocess(OD):
   O, D = OD
   result = osrm_routing_machine(O, D)
   return result

def osrm_routing_machine_multiprocess_all(OD_data):
    results = list(map(osrm_routing_machine_multiprocess, OD_data))
    return results