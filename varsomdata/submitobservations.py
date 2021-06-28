# -*- coding: utf-8 -*-
"""Contains methods for submitting observations to Regobs v5

Modifications:
"""

from __future__ import annotations
import requests
from uuid import uuid4
from enum import IntEnum
from typing import Optional
import pprint
import datetime as dt
import pytz

__author__ = 'arwi'

API = "https://test-api.regobs.no/v4"
TZ = pytz.timezone("Europe/Oslo")
TOKEN = "REPLACEME"
USERNAME = "REPLACEME"
PASSWORD = "REPLACEME"


class Connection:
    class Language(IntEnum):
        NORWEGIAN = 1
        ENGLISH = 2

    def __init__(self, username, password):
        self.expires = None
        self.session = None
        self.guid = None
        self.username = username
        self.password = password
        self.authenticate()

    def authenticate(self) -> Connection:
        login = requests.post(f"{API}/Token/Get", json={"username": self.username, "password": self.password})
        if login.status_code != 200:
            raise AuthError(login.content)
        login = login.json()

        headers = {"Authorization": f"Bearer {login['Access_token']}", "regObs_apptoken": TOKEN}
        self.expires = TZ.localize(dt.datetime.now()) + dt.timedelta(seconds=int(login["Expires_in"]))
        self.session = requests.Session()
        self.session.headers.update(headers)

        guid = self.session.get(f"{API}/Account/Mypage")
        if guid.status_code != 200:
            raise ApiError(guid.content)
        self.guid = guid.json()["Guid"]
        return self

    def submit(self, registration: SnowRegistration, language: Language = 1) -> dict:
        if self.expires < TZ.localize(dt.datetime.now()) + dt.timedelta(seconds=60):
            return self.authenticate().submit(registration)

        if not registration.any_obs:
            raise NoObservationError("No observation in registration.")

        if registration.reg["ObserverGuid"] is None:
            registration.reg["ObserverGuid"] = str(self.guid)

        reg_id = self.session.post(f"{API}/Registration", json=registration.reg)
        if reg_id.status_code != 200:
            raise ApiError(reg_id.content)
        reg_id = reg_id.json()["RegId"]

        returned_reg = self.session.get(f"{API}/Registration/{reg_id}/{int(language)}")
        if returned_reg.status_code != 200:
            raise ApiError(returned_reg.content)
        return returned_reg.json()


class SnowRegistration:
    class Source(IntEnum):
        SEEN = 10
        TOLD = 20
        NEWS = 21
        PICTURE = 22
        ASSUMED = 23

    class SpatialPrecision(IntEnum):
        EXACT = 0
        ONE_HUNDRED = 100
        FIVE_HUNDRED = 500
        ONE_KM = 1000
        OVER_KM = -1

    def __init__(self, obs_time: dt.datetime, lat: float, lon: float,
                 spatial_precision: Optional[SpatialPrecision] = None,
                 source: Optional[Source] = None):

        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise SpatialError("Latitude must be in the range -90--90, longitude -180--180.")

        self.any_obs = False
        self.reg = {
            'AttachmentSummaries': [],
            'Attachments': [],
            'AvalancheActivityObs2': [],
            'AvalancheEvalProblem2': [],
            'AvalancheEvaluation3': None,
            'AvalancheObs': None,
            'CompressionTest': [],
            'DangerObs': [],
            'DtObsTime': obs_time.isoformat(),
            'GeneralObservation': None,
            'GeoHazardTID': 10,
            'ObserverGuid': None,
            'Id': str(uuid4()),
            'Incident': None,
            'ObsLocation': {
                'Latitude': lat,
                'Longitude': lon,
            },
            'SnowProfile2': None,
            'SnowSurfaceObservation': None,
            'WeatherObservation': None,
        }
        if spatial_precision is not None:
            self.reg['ObsLocation']['Uncertainty'] = int(spatial_precision)
        if source is not None:
            self.reg['SourceTID'] = int(source)

    def add_danger_sign(self, danger_sign: DangerSign) -> SnowRegistration:
        self.any_obs = True
        self.reg['DangerObs'].append(danger_sign.obs)
        return self

    def set_note(self, note: Note) -> SnowRegistration:
        self.any_obs = True
        self.reg['GeneralObservation'] = note.obs
        return self


class DangerSign:
    class Sign(IntEnum):
        NO_SIGNS = 1
        RECENT_AVALANCHES = 2
        WHUMPF_SOUND = 3
        RECENT_CRACKS = 4
        LARGE_SNOWFALL = 5
        QUICK_TEMP_CHANGE = 7
        WATER_IN_SNOW = 8
        RECENT_SNOWDRIFT = 9
        OTHER = 99

    def __init__(self, sign: Sign, comment: Optional[str] = None):
        self.obs = {
            'DangerSignTID': int(sign),
        }
        if comment is not None:
            self.obs['Comment'] = comment
        print(self.obs)


class Note:
    def __init__(self, comment: str):
        self.obs = {
            'ObsComment': comment,
            'Urls': [],
        }

    def add_url(self, url: str, description: str) -> Note:
        annotated_url = {
            'UrlDescription': description,
            'UrlLine': url,
        }
        self.obs['Urls'].append(annotated_url)
        return self


class Error(Exception):
    pass


class NoObservationError(Error):
    pass


class AuthError(Error):
    pass


class ApiError(Error):
    pass


class SpatialError(Error):
    pass


class MissingArgumentError(Error):
    pass


if __name__ == "__main__":
    observation_time = TZ.localize(dt.datetime(2021, 6, 16, 10, 15, 0, 0))
    latitude = 68.4293
    longitude = 18.2572

    reg = SnowRegistration(observation_time, latitude, longitude,
                           spatial_precision=SnowRegistration.SpatialPrecision.ONE_HUNDRED,
                           source=SnowRegistration.Source.SEEN)
    reg.add_danger_sign(DangerSign(DangerSign.Sign.WHUMPF_SOUND))
    reg.add_danger_sign(DangerSign(DangerSign.Sign.QUICK_TEMP_CHANGE, "Very quick!"))
    reg.set_note(Note("Demo registration via Python client API.").add_url("https://varsom.no", "Varsom"))

    stored_reg = Connection(USERNAME, PASSWORD).submit(reg, Connection.Language.ENGLISH)
    pprint.pprint(stored_reg)
