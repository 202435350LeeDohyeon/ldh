### help function
# - haversine
import numpy as np
import osmnx as ox

def calculate_straight_distance(lat1, lon1, lat2, lon2):

    km_constant = 3959* 1.609344
    lat1, lon1, lat2, lon2 = map(np.deg2rad, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1 
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a)) 
    km = km_constant * c
    
    return km


def euclid_distance_cal(meter):

    #점 쌍 사이의 유클리드 거리를 계산
    dis_1 = ox.distance.euclidean_dist_vec(36.367658 , 127.447499, 36.443928, 127.419678)
    #직선거리 계산
    dis_2 = ox.distance.great_circle_vec(36.367658 , 127.447499, 36.443928, 127.419678)

    return dis_1/dis_2 * meter