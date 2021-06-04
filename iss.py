import datetime
from math import degrees, pi, sin, cos, radians
import subprocess

import numpy as np
import matplotlib.pyplot as plt
import scipy
import ephem
import json
import geocoder
import requests

OPEN_NOTIFY = "http://api.open-notify.org/iss-now.json"
CELESTRAK = "http://celestrak.com/NORAD/elements/stations.txt"
ELEV_QUERY = "https://www.nationalmap.gov/epqs/pqs.php?x={}&y={}&units=Meters&output=json"
CURL = ["curl", "-X", "GET"]
EARTH_RADIUS = 6.3781E6

def latlong2ecef(lat, long, elev):
    dist = EARTH_RADIUS + elev
    z = dist * sin(radians(lat))
    x = dist * cos(radians(lat)) * cos(radians(long))
    y = dist * cos(radians(lat)) * sin(radians(long))
    return x, y, z


def rotate_y(theta, state=None):
    Yrot = np.zeros((3, 3))
    Yrot[:, 0] = [cos(radians(theta)), 0, -sin(radians(theta))]
    Yrot[:, 1] = [0, 1, 0]
    Yrot[:, 2] = [sin(radians(theta)), 0, cos(radians(theta))]
    if state is None:
        return Yrot
    else:
        return Yrot * state


def rotate_z(theta, state=None):
    Zrot = np.zeros((3, 3))
    Zrot[:, 0] = [cos(radians(theta)), sin(radians(theta)), 0]
    Zrot[:, 1] = [-sin(radians(theta)), cos(radians(theta)), 0]
    Zrot[:, 2] = [0, 0, 1]
    if state is None:
        return Zrot
    else:
        return Zrot * state


def translate_point(point, origin):
    return point - origin


def nedframe_rotmat(lat, long, point=None):
    rot_mat = rotate_z(long) @ rotate_y(-lat) @ rotate_y(-90)
    if point is None:
        return rot_mat
    else:
        return rot_mat @ point


def main():
    my_angles = np.zeros((3,))
    my_xyz = np.zeros((3,))
    g = geocoder.ip("me")
    my_angles[:2] = g.latlng
    CURL.append(ELEV_QUERY.format(my_angles[1], my_angles[0]))
    elev_str = subprocess.check_output(CURL)
    elev_data = json.loads(elev_str)
    my_angles[2] = float(elev_data["USGS_Elevation_Point_Query_Service"]["Elevation_Query"]["Elevation"])
    print("\nMy Lat: {}, My Long: {}, My Elevation: {}".format(my_angles[0], my_angles[1], my_angles[2]))

    my_xyz[:] = latlong2ecef(my_angles[0], my_angles[1], my_angles[2])
    print("My X: {}, My Y: {}, My Z: {}".format(my_xyz[0], my_xyz[1], my_xyz[2]))

    ned_rotmat = nedframe_rotmat(my_angles[0], my_angles[1])
    print("My NED Frame Rotation Matrix:\n{}\n".format(ned_rotmat))

    celes_req = requests.get(CELESTRAK)
    txtdata = celes_req.text.split("\r\n")
    for i in range(0, 3, len(txtdata)):
        if "ISS" in txtdata[i]:
            line0 = txtdata[i].strip()
            line1 = txtdata[i + 1].strip()
            line2 = txtdata[i + 2].strip()
            break

    print("ISS Ephemeris Data (TLE)")
    print(line0)
    print(line1)
    print(line2)

    iss_angles = np.zeros((3,))
    iss_xyz = np.zeros((3,))
    iss = ephem.readtle(line0, line1, line2)
    now = datetime.datetime.utcnow()
    iss.compute(now)
    #  iss_angles[:] = degrees(iss.sublat), degrees(iss.sublong), iss.elevation
    iss_angles[:] = 25.7743, -80.1937, 0
    print("ISS Lat: {}, ISS Lon: {}, ISS Elevation: {}".format(iss_angles[0], iss_angles[1], iss_angles[2]))

    iss_xyz[:] = latlong2ecef(iss_angles[0], iss_angles[1], iss_angles[2])
    print("ISS X: {}, ISS Y: {}, ISS Z: {}\n".format(iss_xyz[0], iss_xyz[1], iss_xyz[2]))

    # ISS In Observer NED (North-East-Down) Frame.
    # This is a Local Tangent Plane for an observer on the Earth's surface.
    # First, translate ECEF coordinates of ISS to observer origin reference frame
    # Then, rotate the result by the NED rotation matrix
    iss_translate = translate_point(iss_xyz, my_xyz)
    print("ISS translated to observer origin reference frame:\n{}".format(iss_translate))

    iss_rotate = ned_rotmat.T @ iss_translate
    print("ISS rotated to observer NED frame:\n{}".format(iss_rotate))

    iss_direction = iss_rotate / np.linalg.norm(iss_rotate)
    print("Direction unit vector of ISS from observer:\n{}\n".format(iss_direction))


if __name__ == "__main__":
    main()
