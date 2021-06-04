import datetime

import numpy as np


def calc_epoch(epoch):
    date, time = epoch.split(".")


def get_orb_params(filename):
    with open(filename, "r") as f:
        lines = f.readlines()

    name = lines[0].strip()
    line1 = lines[1].strip().split()
    line2 = lines[2].strip().split()

    # inclination
    inclination = float(line2[2])

    # right ascension of ascending node
    raan = float(line2[3])

    # eccentricity
    e_string = "0." + line2[4]
    e = float(e_string)

    # argument of perigee
    aop = float(line2[5])

    # mean anomaly
    mean_anom = float(line2[6])

    # mean motion
    mean_mot = float(line2[7])  # num revs per day

    # orbital period (hours)
    period_hrs = 1.0 / mean_mot * 24.0
    period_days = period_hrs / 24.0
    period_min = period_hrs * 60
    period_sec = period_hrs * 3600
