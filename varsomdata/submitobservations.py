# -*- coding: utf-8 -*-
"""Contains methods for submitting observations to Regobs v5

Modifications:
"""

from __future__ import annotations
import requests
from enum import IntEnum, Enum
from typing import Optional
import pprint
import datetime as dt
import pytz

__author__ = 'arwi'

API = "https://test-api.regobs.no/v5"
TZ = pytz.timezone("Europe/Oslo")
TOKEN = "REPLACEME"
USERNAME = "REPLACEME"
PASSWORD = "REPLACEME"
EXPIRES_IN = 3600


class Connection:
    class Language(IntEnum):
        NORWEGIAN = 1
        ENGLISH = 2

    def __init__(self, username: str, password: str, token: str):
        self.expires = None
        self.session = None
        self.guid = None
        self.username = username
        self.password = password
        self.token = token
        self.authenticate()

    def authenticate(self) -> Connection:
        headers = {"regObs_apptoken": self.token}
        self.session = requests.Session()
        self.session.headers.update(headers)

        login = self.session.post(f"{API}/Account/Token", json={"username": self.username, "password": self.password})
        if login.status_code != 200:
            raise AuthError(login.content)
        token = login.json()

        headers["Authorization"] = f"Bearer {token}"
        self.session.headers.update(headers)
        self.expires = TZ.localize(dt.datetime.now()) + dt.timedelta(seconds=EXPIRES_IN)

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

        #if registration.reg["ObserverGuid"] is None:
        #    registration.reg["ObserverGuid"] = str(self.guid)

        reg_filtered = {k: v for k, v in registration.reg.items() if v}
        reg_id = self.session.post(f"{API}/Registration", json=reg_filtered)
        if reg_id.status_code != 200:
            raise ApiError(reg_id.content)
        reg_id = reg_id.json()["RegId"]

        returned_reg = self.session.get(f"{API}/Registration/{reg_id}/{language}")
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

    def __init__(self, obs_time: dt.datetime, position: Position,
                 spatial_precision: Optional[SpatialPrecision] = None,
                 source: Optional[Source] = None):
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
            #'ObserverGuid': None,
            #'Id': str(uuid4()),
            'Incident': None,
            'ObsLocation': {
                'Latitude': position.lat,
                'Longitude': position.lon,
                'Uncertainty': spatial_precision,
            },
            'SourceTID': source,
            'SnowProfile2': None,
            'SnowSurfaceObservation': None,
            'WeatherObservation': None,
        }

    def add_danger_sign(self, danger_sign: DangerSign) -> SnowRegistration:
        self.any_obs = True
        self.reg['DangerObs'].append(danger_sign.obs)
        return self

    def set_avalanche_obs(self, avalanche_obs: AvalancheObs) -> SnowRegistration:
        self.any_obs = True
        self.reg['AvalancheObs'] = avalanche_obs.obs
        return self

    def add_avalanche_activity(self, avalanche_activity: AvalancheActivity) -> SnowRegistration:
        self.any_obs = True
        self.reg['AvalancheActivityObs2'].append(avalanche_activity.obs)
        return self

    def set_weather(self, weather: Weather) -> SnowRegistration:
        self.any_obs = True
        self.reg["WeatherObservation"] = weather.obs
        return self

    def set_snow_cover(self, snow_cover: SnowCover) -> SnowRegistration:
        self.any_obs = True
        self.reg["SnowSurfaceObservation"] = snow_cover.obs
        return self

    # Tests

    # Snow Profile

    def add_avalanche_problem(self, avalanche_problem: AvalancheProblem):
        self.any_obs = True
        self.reg["AvalancheEvalProblem2"].append(avalanche_problem.obs)
        return self

    def set_danger_assessment(self, danger_assessment: DangerAssessment):
        self.any_obs = True
        self.reg["AvalancheEvaluation3"] = danger_assessment.obs
        return self

    def set_incident(self, incident: Incident) -> SnowRegistration:
        self.any_obs = True
        self.reg['Incident'] = incident.obs
        return self

    def set_note(self, note: Note) -> SnowRegistration:
        self.any_obs = True
        self.reg['GeneralObservation'] = note.obs
        return self


class Observation:
    def __init__(self, obs):
        self.obs = {k: v for k, v in obs.items() if v is not None}


class DangerSign(Observation):
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

    def __init__(self,
                 sign: Optional[Sign] = None,
                 comment: Optional[str] = None):
        if all(e is None for e in [sign, comment]):
            raise NoObservationError("No argument passed to danger sign observation.")

        obs = {
            'DangerSignTID': sign if sign is not None else 0,
            'Comment': comment,
        }
        super().__init__(obs)


class AvalancheObs(Observation):
    class Type(IntEnum):
        DRY_LOOSE = 12
        WET_LOOSE = 11
        DRY_SLAB = 22
        WET_SLAB = 21
        GLIDE = 27
        SLUSH_FLOW = 30
        CORNICE = 40
        UNKNOWN = 99

    class Trigger(IntEnum):
        NATURAL = 10
        HUMAN = 26
        SNOWMOBILE = 27
        REMOTE = 22
        TEST_SLOPE = 23
        EXPLOSIVES = 25
        UNKNOWN = 99

    class Terrain(IntEnum):
        STEEP_SLOPE = 10
        LEE_SIDE = 20
        CLOSE_TO_RIDGE = 30
        GULLY = 40
        SLAB = 50
        BOWL = 60
        FOREST = 70
        LOGGING_AREA = 75
        EVERYWHERE = 95
        UNKNOWN = 99

    def __init__(self, release_time: dt.datetime,
                 start: Optional[Position] = None,
                 stop: Optional[Position] = None,
                 exposition: Optional[Direction] = None,
                 size: Optional[DestructiveSize] = None,
                 avalanche_type: Optional[Type] = None,
                 trigger: Optional[Trigger] = None,
                 terrain: Optional[Terrain] = None,
                 weak_layer: Optional[WeakLayer] = None,
                 fracture_height_cm: Optional[int] = None,
                 fracture_width: Optional[int] = None,
                 path_name: Optional[str] = None,
                 comment: Optional[str] = None,
                 ):
        obs = {
            'AvalCauseTID': weak_layer,
            'AvalancheTID': avalanche_type,
            'AvalancheTriggerTID': trigger,
            'Comment': comment,
            'DestructiveSizeTID': size,
            'DtAvalancheTime': release_time.isoformat(),
            'FractureHeight': fracture_height_cm,
            'FractureWidth': fracture_width,
            'StartLat': start.lat if start is not None else None,
            'StartLong': start.lon if start is not None else None,
            'StopLat': stop.lat if stop is not None else None,
            'StopLong': stop.lon if stop is not None else None,
            'TerrainStartZoneTID': terrain,
            'Trajectory': path_name,
            'ValidExposition': Expositions([exposition]).exp if exposition is not None else None,
        }
        super().__init__(obs)


class AvalancheActivity(Observation):
    class Timeframe(Enum):
        ZERO_TO_SIX = '0-6'
        SIX_TO_TWELVE = '6-12'
        TWELVE_TO_EIGHTEEN = '12-18'
        EIGHTEEN_TO_TWENTY_FOUR = '18-24'

    class Quantity(IntEnum):
        NO_ACTIVITY = 1
        ONE = 2
        FEW = 3
        SEVERAL = 4
        NUMEROUS = 5

    class Type(IntEnum):
        DRY_LOOSE = 10
        WET_LOOSE = 15
        DRY_SLAB = 20
        WET_SLAB = 25
        GLIDE = 27
        SLUSH_FLOW = 30
        CORNICE = 40

    def __init__(self, date: dt.date,
                 timeframe: Optional[Timeframe] = None,
                 quantity: Optional[Quantity] = None,
                 avalanche_type: Optional[Type] = None,
                 sensitivity: Optional[Sensitivity] = None,
                 size: Optional[DestructiveSize] = None,
                 distribution: Optional[Distribution] = None,
                 elevation: Optional[Elevation] = None,
                 expositions: Optional[Expositions] = None,
                 comment: Optional[str] = None):
        avalanche_attributes = [quantity, avalanche_type, sensitivity, size, distribution, elevation, expositions]
        if quantity == self.Quantity.NO_ACTIVITY and any(e is not None for e in avalanche_attributes):
            raise NoObservationError("Avalanche attributes specified, but no avalanche activity reported.")

        timeframe_times = {
            None: {'start': dt.time(0), 'end': dt.time(23, 59)},
            '0-6': {'start': dt.time(0), 'end': dt.time(6)},
            '6-12': {'start': dt.time(6), 'end': dt.time(12)},
            '12-18': {'start': dt.time(12), 'end': dt.time(18)},
            '18-24': {'start': dt.time(18), 'end': dt.time(23, 59)},
        }[timeframe.value if timeframe is not None else None]
        start = TZ.localize(dt.datetime.combine(date, timeframe_times['start']))
        end = TZ.localize(dt.datetime.combine(date, timeframe_times['end']))

        obs = {
            'AvalPropagationTID': distribution,
            'AvalTriggerSimpleTID': sensitivity,
            'AvalancheExtTID': avalanche_type,
            'Comment': comment,
            'DestructiveSizeTID': size,
            'DtEnd': end.isoformat(),
            'DtStart': start.isoformat(),
            'EstimatedNumTID': quantity,
            'ValidExposition': expositions.exp,
        }
        if elevation is not None:
            obs = {**obs, **elevation.elev}
        super().__init__(obs)


class Weather(Observation):
    class Precipitation(IntEnum):
        NO_PRECIPITATION = 1
        DRIZZLE = 2
        RAIN = 3
        SLEET = 4
        SNOW = 5
        HAIL = 6
        FREEZING_RAIN = 8

    def __init__(self,
                 precipitation: Optional[Precipitation] = None,
                 wind_dir: Optional[Direction] = None,
                 air_temp: Optional[float] = None,
                 wind_speed: Optional[float] = None,
                 cloud_cover: Optional[int] = None,
                 comment: Optional[str] = None):
        if all(e is None for e in [precipitation, air_temp, wind_speed, cloud_cover, wind_dir, comment]):
            raise NoObservationError("No argument passed to weather observation.")
        if cloud_cover is not None and not (0 <= cloud_cover <= 100):
            raise PercentError("Percentage must be within the range 0--100.")

        obs = {
            'AirTemperature': air_temp,
            'CloudCover': cloud_cover,
            'Comment': comment,
            'PrecipitationTID': precipitation,
            'WindDirection': wind_dir * 45 if wind_dir is not None else None,
            'WindSpeed': wind_speed
        }
        super().__init__(obs)


class SnowCover(Observation):
    class Drift(IntEnum):
        NO_DRIFT = 1
        SOME = 2
        MODERATE = 3
        HEAVY = 4

    class Surface(IntEnum):
        LOOSE_OVER_30_CM = 101
        LOOSE_10_TO_30_CM = 102
        LOOSE_1_TO_10_CM = 103
        SURFACE_HOAR_HARD = 61
        SURFACE_HOAR_SOFT = 62
        NEW_SURFACE_FACETS = 50
        CRUST = 107
        WIND_SLAB_HARD = 105
        STORM_SLAB_SOFT = 106
        WET_LOOSE = 104
        OTHER = 108

    class Moisture(IntEnum):
        NO_SNOW = 1
        DRY = 2
        MOIST = 3
        WET = 4
        VERY_WET = 5
        SLUSH = 6

    def __init__(self,
                 drift: Optional[Drift] = None,
                 surface: Optional[Surface] = None,
                 moisture: Optional[Moisture] = None,
                 hn24_cm: Optional[float] = None,
                 new_snow_line: Optional[int] = None,
                 hs_cm: Optional[float] = None,
                 snow_line: Optional[int] = None,
                 layered_snow_line: Optional[float] = None,
                 comment: Optional[str] = None):
        if all(e is None for e in
               [drift, surface, moisture, hn24_cm, new_snow_line, hs_cm, snow_line, layered_snow_line, comment]):
            raise NoObservationError("No argument passed to snow cover observation.")

        obs = {
            'Comment': comment,
            'HeightLimitLayeredSnow': layered_snow_line,
            'NewSnowDepth24': hn24_cm / 100 if hn24_cm is not None else None,
            'NewSnowLine': new_snow_line,
            'SnowDepth': hs_cm / 100 if hs_cm is not None else None,
            'SnowDriftTID': drift,
            'SnowLine': snow_line,
            'SnowSurfaceTID': surface,
            'SurfaceWaterContentTID': moisture,
        }
        super().__init__(obs)


class AvalancheProblem(Observation):
    class LayerDepth(IntEnum):
        LESS_THAN_50_CM = 1
        LESS_THAN_100_CM = 2
        MORE_THAN_100_CM = 3

    class Type(IntEnum):
        DRY_LOOSE = 10
        WET_LOOSE = 15
        DRY_SLAB = 20
        WET_SLAB = 25

    def __init__(self,
                 weak_layer: Optional[WeakLayer] = None,
                 layer_depth: Optional[LayerDepth] = None,
                 avalanche_type: Optional[Type] = None,
                 sensitivity: Optional[Sensitivity] = None,
                 size: Optional[DestructiveSize] = None,
                 distribution: Optional[Distribution] = None,
                 elevation: Optional[Elevation] = None,
                 expositions: Optional[Expositions] = None,
                 is_easy_propagation: Optional[bool] = None,
                 is_layer_thin: Optional[bool] = None,
                 is_soft_slab_above: Optional[bool] = None,
                 is_large_crystals: Optional[bool] = None,
                 comment: Optional[str] = None):
        if all(e is None for e in
               [weak_layer, layer_depth, avalanche_type, sensitivity, size, distribution, elevation, expositions,
                is_easy_propagation, is_layer_thin, is_soft_slab_above, is_large_crystals, comment]):
            raise NoObservationError("No argument passed to avalanche problem assessment.")

        obs = {
            'AvalCauseTID': weak_layer,
            'AvalCauseDepthTID': layer_depth,
            'AvalCauseAttributeLightTID': 1 if is_easy_propagation else None,
            'AvalCauseAttributeThinTID': 2 if is_layer_thin else None,
            'AvalCauseAttributeSoftTID': 4 if is_soft_slab_above else None,
            'AvalCauseAttributeCrystalTID': 8 if is_large_crystals else None,
            'AvalancheExtTID': avalanche_type,
            'AvalTriggerSimpleTID': sensitivity,
            'DestructiveSizeTID': size,
            'AvalPropagationTID': distribution,
            'Comment': comment,
            'ValidExposition': expositions.exp,
        }
        if elevation is not None:
            obs = {**obs, **elevation.elev}
        super().__init__(obs)


class DangerAssessment(Observation):
    class DangerLevel(IntEnum):
        ONE_LOW = 1
        TWO_MODERATE = 2
        THREE_CONSIDERABLE = 3
        FOUR_HIGH = 4
        FIVE_EXTREME = 5

    class ForecastEvaluation(IntEnum):
        CORRECT = 1
        TOO_LOW = 2
        TOO_HIGH = 3

    def __init__(self,
                 danger_level: Optional[DangerLevel] = None,
                 forecast_evaluation: Optional[ForecastEvaluation] = None,
                 danger_assessment: Optional[str] = None,
                 danger_development: Optional[str] = None,
                 comment: Optional[str] = None):
        if all(e is None for e in [danger_level, forecast_evaluation, danger_assessment, danger_development, comment]):
            raise NoObservationError("No argument passed to avalanche danger assessment.")

        obs = {
            'AvalancheDangerTID': danger_level,
            'ForecastCorrectTID': forecast_evaluation,
            'AvalancheEvaluation': danger_assessment,
            'AvalancheDevelopment': danger_development,
            'ForecastComment': comment,
        }
        super().__init__(obs)


class Incident(Observation):
    class Activity(IntEnum):
        BACKCOUNTRY = 111
        OFF_PISTE = 113
        RESORT = 112
        NORDIC = 114
        CROSS_COUNTRY = 115
        CLIMBING = 116
        FOOT = 117
        SNOWMOBILE = 130
        ROAD = 120
        RAILWAY = 140
        BUILDING = 160
        OTHER = 190

    class Extent(IntEnum):
        NO_EFFECT = 10
        SAR = 13
        TRAFFIC = 15
        EVACUATION = 25
        MATERIAL_ONLY = 20
        CLOSE_CALL = 27
        BURIAL_UNHARMED = 28
        PEOPLE_HURT = 30
        FATAL = 40
        OTHER = 99

    def __init__(self,
                 activity: Optional[Activity] = None,
                 extent: Optional[Extent] = None,
                 comment: Optional[str] = None):
        if all(e is None for e in [activity, extent, comment]):
            raise NoObservationError("No argument passed to incident observation.")

        obs = {
            'ActivityInfluencedTID': activity,
            'Comment': comment,
            'DamageExtentTID': extent,
            'IncidentURLs': [],
        }
        super().__init__(obs)

    def add_url(self, url: Url) -> Incident:
        self.obs['IncidentURLs'].append(url.url)
        return self


class Note(Observation):
    def __init__(self, comment: str):
        obs = {
            'ObsComment': comment,
            'Urls': [],
        }
        super().__init__(obs)

    def add_url(self, url: Url) -> Note:
        self.obs['Urls'].append(url.url)
        return self


class Url:
    def __init__(self, url: str, description: str):
        self.url = {
            'UrlDescription': description,
            'UrlLine': url,
        }


class DestructiveSize(IntEnum):
    D1 = 1
    D2 = 2
    D3 = 3
    D4 = 4
    D5 = 5
    UNKNOWN = 9


class Sensitivity(IntEnum):
    VERY_DIFFICULT = 30
    DIFFICULT = 40
    EASY = 50
    VERY_EASY = 60
    SPONTANEOUS = 22


class Distribution(IntEnum):
    ISOLATED = 1
    SPECIFIC = 2
    WIDESPREAD = 3


class WeakLayer(IntEnum):
    PP = 10
    SH = 11
    FC_NEAR_SURFACE = 13
    BONDING_ABOVE_MFCR = 14
    DF = 15
    DH = 16
    FC_BELOW_MFCR = 19
    FC_ABOVE_MFCR = 18
    WATER_IN_SNOW = 22
    GROUND_MELT = 20
    LOOSE_SNOW = 24


class Position:
    def __init__(self, lat: float, lon: float):
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise SpatialError("Latitude must be in the range -90--90, longitude -180--180.")

        self.lat = lat
        self.lon = lon


class Elevation:
    class Format(IntEnum):
        ABOVE = 1
        BELOW = 2
        SANDWICH = 3
        MIDDLE = 4

    def __init__(self, elev_fmt: Format, elev: int,
                 elev_secondary: Optional[int] = None):
        if not (0 <= elev <= 2500) or (elev_secondary is not None and not (0 <= elev_secondary <= 2500)):
            raise ElevationError("Elevations must be in the range 0--2500 m.a.s.l.")
        if (elev_fmt == self.Format.ABOVE or elev_fmt == self.Format.BELOW) and elev_secondary is not None:
            raise ElevationError("ABOVE and BELOW elevation formats does not use parameter elev_secondary.")
        elif (elev_fmt == self.Format.SANDWICH or elev_fmt == self.Format.MIDDLE) and elev_secondary is None:
            raise ElevationError("SANDWICH and MIDDLE elevation formats must use parameter elev_secondary.")

        if elev_secondary is not None:
            elev_max = round(max(elev, elev), -2)
            elev_min = round(min(elev, elev_secondary), -2)
            elev_min -= 100 if elev_max == elev_min else 0
        else:
            elev_max = elev
            elev_min = None

        self.elev = {
            'ExposedHeightComboTID': elev_fmt,
            'ExposedHeight1': elev_max,
            'ExposedHeight2': elev_min,
        }


class Expositions:
    def __init__(self, expositions: [Direction]):
        self.exp = "00000000"
        for exposition in expositions:
            self.exp = self.exp[:exposition] + "1" + self.exp[exposition + 1:]


class Direction(IntEnum):
    N = 0
    NE = 1
    E = 2
    SE = 3
    S = 4
    SW = 5
    W = 6
    NW = 7


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


class ElevationError(Error):
    pass


class PercentError(Error):
    pass


class MissingArgumentError(Error):
    pass


if __name__ == "__main__":
    reg = SnowRegistration(TZ.localize(dt.datetime(2021, 6, 16, 10, 15)),
                           Position(lat=68.4293, lon=18.2572),
                           SnowRegistration.SpatialPrecision.ONE_HUNDRED,
                           SnowRegistration.Source.SEEN)

    reg.add_danger_sign(DangerSign(DangerSign.Sign.WHUMPF_SOUND))
    reg.add_danger_sign(DangerSign(DangerSign.Sign.QUICK_TEMP_CHANGE, "Very quick!"))
    reg.add_danger_sign(DangerSign(comment="It just felt dangerous."))

    reg.set_avalanche_obs(AvalancheObs(TZ.localize(dt.datetime(2021, 3, 21, 16, 5)),
                                       Position(lat=61.1955, lon=10.3711),
                                       Position(lat=60.8071, lon=7.9102),
                                       Direction.NE,
                                       DestructiveSize.D3,
                                       AvalancheObs.Type.DRY_SLAB,
                                       AvalancheObs.Trigger.NATURAL,
                                       AvalancheObs.Terrain.CLOSE_TO_RIDGE,
                                       WeakLayer.GROUND_MELT,
                                       fracture_height_cm=225,
                                       fracture_width=700,
                                       path_name="Path A",
                                       comment="Extremely long path."))

    reg.add_avalanche_activity(AvalancheActivity(dt.date(2021, 2, 25),
                                                 AvalancheActivity.Timeframe.SIX_TO_TWELVE,
                                                 AvalancheActivity.Quantity.FEW,
                                                 AvalancheActivity.Type.DRY_SLAB,
                                                 Sensitivity.SPONTANEOUS,
                                                 DestructiveSize.D4,
                                                 Distribution.SPECIFIC,
                                                 Elevation(Elevation.Format.ABOVE, 500),
                                                 Expositions([Direction.NE, Direction.S]),
                                                 "Avalanche activity above 500 masl"))

    reg.set_weather(Weather(Weather.Precipitation.DRIZZLE,
                            Direction.NE,
                            wind_speed=2.2,
                            cloud_cover=15))

    reg.set_snow_cover(SnowCover(SnowCover.Drift.MODERATE,
                                 SnowCover.Surface.WIND_SLAB_HARD,
                                 hn24_cm=9.2,
                                 new_snow_line=101,
                                 hs_cm=243.7,
                                 snow_line=2300,
                                 layered_snow_line=203.6))

    reg.add_avalanche_problem(AvalancheProblem(WeakLayer.FC_ABOVE_MFCR,
                              AvalancheProblem.LayerDepth.LESS_THAN_50_CM,
                              AvalancheProblem.Type.DRY_SLAB,
                              Sensitivity.VERY_EASY,
                              DestructiveSize.D3,
                              Distribution.SPECIFIC,
                              Elevation(Elevation.Format.ABOVE, 500),
                              Expositions([Direction.N, Direction.NE]),
                              is_easy_propagation=True,
                              is_layer_thin=True,
                              is_soft_slab_above=False,
                              is_large_crystals=False,
                              comment="A sketchy persistent weak slab."))

    reg.set_danger_assessment(DangerAssessment(DangerAssessment.DangerLevel.FOUR_HIGH,
                                               DangerAssessment.ForecastEvaluation.TOO_LOW,
                                               "It's very dangerous out there.",
                                               "I hope tomorrow is better.",
                                               "This is a comment."))

    reg.set_incident(Incident(Incident.Activity.CLIMBING,
                              Incident.Extent.CLOSE_CALL,
                              "Scary."
                              ).add_url(Url("https://nve.no", "NVE")))

    reg.set_note(Note("Demo registration via Python client API."
                      ).add_url(Url("https://varsom.no", "Varsom")))

    stored_reg = Connection(USERNAME, PASSWORD, TOKEN).submit(reg, Connection.Language.ENGLISH)
    pprint.pprint(stored_reg)
