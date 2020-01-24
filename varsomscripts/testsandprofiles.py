# -*- coding: utf-8 -*-
"""Module for calculating and plotting overall performance of Regobs."""

import setenvironment as env
from varsomdata import getvarsompickles as gvp
from varsomdata import getobservations as go
import collections as cols
import logging as lg

__author__ = 'ragnarekker'


def _str(s):
    """Wash the strings."""

    if s is None:
        s = ''

    if s == 'Ikke gitt':
        s = ''

    if s == 'Ikke spesifisert':
        s = ''

    return str(s)


class TestsAndLayerInfo:

    def __init__(self, t, p):

        self.result = t.PropagationName
        self.test = None
        self.pnx = None
        self.depth = t.FractureDepth
        self.taps = t.TapsFracture
        self.fracture = t.ComprTestFractureName
        self.url = f"{env.registration_basestring}{t.RegID}"
        self.obstime = str(t.DtObsTime)
        self.forecast_region_name = t.ForecastRegionName
        self.forecast_region_tid = t.ForecastRegionTID

        self.layer_thickness = None
        self.layer_grain_form = None
        self.layer_grain_size = None
        self.layer_hardness = None
        self.layer_hardness_id = None

        self.above_layer_thickness = None
        self.above_layer_grain_form = None
        self.above_layer_grain_size = None
        self.above_layer_hardness = None
        self.above_layer_hardness_id = None

        self.below_layer_thickness = None
        self.below_layer_grain_form = None
        self.below_layer_grain_size = None
        self.below_layer_hardness = None
        self.below_layer_hardness_id = None

        self._set_test()
        self._set_pnx()

        if self.depth:      # Only given if there is a fracture somewhere
            if p:
                self._set_layer_info(p)

        self.original_test = t
        self.original_profile = p

    def _set_test(self):
        if 'ECT' in self.result:
            self.test = 'ECT'
        elif 'CT' in self.result:
            self.test = 'CT'

    def _set_pnx(self):

        if self.result == 'ECTX' or self.result == 'CTN':
            self.pnx = 'X'
        elif 'ECTP' in self.result:
            self.pnx = 'P'
        elif 'ECTN' in self.result:
            self.pnx = 'N'

    def _set_layer_info(self, p):

        l_index = 0
        layer_selected = False
        if p.StratProfile:

            for l in p.StratProfile:
                if layer_selected is False:
                    # if test result in a boundary,
                    # and it is not at the top by faulty observation,
                    # find which layer is the loosest (lower TID for looser layer)
                    # and choose this for the layer we are studying
                    # else, go back one layer and choose this
                    if l.DepthTop == self.depth:
                        if l_index > 0:
                            if l.HardnessTID <= p.StratProfile[l_index-1].HardnessTID:
                                layer_selected = True
                            else:
                                l_index -= 1
                                l = p.StratProfile[l_index]
                                layer_selected = True

                    # else if test is in a layer, all is clear
                    elif l.DepthTop < self.depth < (l.DepthTop + l.Thickness):
                        layer_selected = True

                    if layer_selected:
                        self.layer_thickness = l.Thickness
                        self.layer_grain_form = l.GrainFormPrimaryName
                        self.layer_grain_size = l.GrainSizeAvg
                        self.layer_hardness = l.HardnessName
                        self.layer_hardness_id = l.HardnessTID

                        if l_index > 0:
                            self.above_layer_thickness = p.StratProfile[l_index-1].Thickness
                            self.above_layer_grain_form = p.StratProfile[l_index-1].GrainFormPrimaryName
                            self.above_layer_grain_size = p.StratProfile[l_index-1].GrainSizeAvg
                            self.above_layer_hardness = p.StratProfile[l_index-1].HardnessName
                            self.above_layer_hardness_id = p.StratProfile[l_index-1].HardnessTID

                        if len(p.StratProfile) > l_index + 1:
                            self.below_layer_thickness = p.StratProfile[l_index+1].Thickness
                            self.below_layer_grain_form = p.StratProfile[l_index+1].GrainFormPrimaryName
                            self.below_layer_grain_size = p.StratProfile[l_index+1].GrainSizeAvg
                            self.below_layer_hardness = p.StratProfile[l_index+1].HardnessName
                            self.below_layer_hardness_id = p.StratProfile[l_index+1].HardnessTID

                    l_index += 1

    def to_ord_dict(self):

        _ord_dict = cols.OrderedDict([
            ('Result', self.result),
            ('Test', self.test),
            ('PNX', self.pnx),
            ('Depth', self.depth),
            ('Taps', self.taps),
            ('Fracture', self.fracture),
            ('Layer thick', self.layer_thickness),
            ('Layer grain', self.layer_grain_form),
            ('Layer grain Ø', self.layer_grain_size),
            ('Layer hardness', self.layer_hardness),
            ('Above thick', self.above_layer_thickness),
            ('Above grain', self.above_layer_grain_form),
            ('Above grain Ø', self.above_layer_grain_size),
            ('Above hardness', self.above_layer_hardness),
            ('Below thick', self.below_layer_thickness),
            ('Below grain', self.below_layer_grain_form),
            ('Below grain Ø', self.below_layer_grain_size),
            ('Below hardness', self.below_layer_hardness),
            ('Region', self.forecast_region_name),
            ('Region ID', self.forecast_region_tid),
            ('Obs time', self.obstime),
            ('URL', self.url)
        ])

        return _ord_dict


def get_tests_and_layer_info_to_gustav():

    years = ['2019-20', '2018-19', '2017-18', '2016-17']
    # years = ['2018-19']

    all_observations = []
    for y in years:
        all_observations += gvp.get_all_observations(y)

    tests = []

    for o in all_observations:
        for f in o.Observations:
            if isinstance(f, go.ColumnTest) or isinstance(f, go.ProfileColumnTest):
                if f.CompetenceLevelTID >= 120:
                    if 'Ikke gitt' not in f.PropagationName:

                        profile = None
                        if f.IncludeInSnowProfile:
                            for tf in o.Observations:
                                if isinstance(tf, go.SnowProfile):
                                    profile = tf

                        tests.append(TestsAndLayerInfo(f, profile))

    file_and_folder = f'{env.output_folder}tests_to_gustav_pless.csv'

    # Write  to file
    with open(file_and_folder, 'w', encoding='utf-8') as f:
        make_header = True
        for t in tests:
            if make_header:
                f.write(';'.join([_str(d) for d in t.to_ord_dict().keys()]) + '\n')
                make_header = False
            f.write(';'.join([_str(d) for d in t.to_ord_dict().values()]) + '\n')

    a = 1


if __name__ == '__main__':

    get_tests_and_layer_info_to_gustav()
