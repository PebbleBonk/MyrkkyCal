#! -*- coding: utf-8 -*-
import re
import params
# "course_code": [r'[A-Z]+-[A-Z]\d+',  # ELEC
#                 r'\d{2}[A-Z]\d{5}',  # Business
#                 r'[A-Za-z]+-\d+.\d+']  # Languages

BLDNG_TAG = "building"
ADDRS_TAG = "address"
CLSRM_TAG = "classroom"
CCODE_TAG = "course_code"
CNAME_TAG = "course_name"
EVENT_TAG = "event_type"
DETAL_TAG = "course_details"
ERROR_TAG = "errors"
SUMMR_TAG = "summary"
LOCAT_TAG = "location"
TIMES_TAG = "timestamp"


def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)


class Identifier(object):

    info_types = {CLSRM_TAG: [r'([A-Z]*\d+-*\d+[a-z]*) \(\1\)',
                              r'[\w-]+ / \w+',
                              r'[^-][A-Z]\d{3}'],

                  ADDRS_TAG: [r'[\w-]+ \d{1,3} ?[A-Za-z]?'],
                  EVENT_TAG: [r'([A-Z]\d{2}|[A-Z]{2}\d)[\w ]*/[\w ]*/[\w ]*'],
                  DETAL_TAG: [r'[A-Z]+-[\d\w]+ - [\w ]+'],
                  TIMES_TAG: [r'\d{1,2}\.\d{1,2}\.\d{2,4}']}

    def __init__(self):
        self.best_guess = None
        self.guesses = {}
        self.tag_types = []

    def identify_tag_type(self, tag):
        tag_types = []
        # info_types = Identifier.info_types
        # for infotype in info_types:
        # 	if any([re.search(f, tag) for f in info_types[infotype]]):
        # 		tag_types.append(infotype)
        self._identify_as_event_type(tag)
        self._identify_as_classroom(tag)
        self._identify_as_address(tag)
        self._identify_as_detail(tag)

        tag_types = self.tag_types
        if len(tag_types) == 0 and \
           not hasNumbers(tag) and \
           len(tag) < params.BLDNG_TH:
            tag_types.append(BLDNG_TAG)
        if len(tag_types) == 0 and not hasNumbers(tag):
            tag_types.append(EVENT_TAG)
        print(tag_types)
        return tag_types

# IDENTIFIERS:
    def _identify_as_classroom(self, tag):
        # TODO
        amp = 0
        if self._default_validation(tag, CLSRM_TAG):
            amp += 1

        self._update_lists(CLSRM_TAG, amp)
        return amp

    def _identify_as_address(self, tag):
        # TODO
        amp = 0
        if self._default_validation(tag, ADDRS_TAG):
            amp += 1
        self._update_lists(ADDRS_TAG, amp)
        return amp

    def _identify_as_event_type(self, tag):
        # TODO
        amp = 0
        if self._default_validation(tag, EVENT_TAG):
            amp += 1
        if any(kw in tag for kw in params.EVENT_TYPE_KEYWORDS):
            amp += 1
        self._update_lists(EVENT_TAG, amp)
        return amp

    def _identify_as_detail(self, tag):
        # TODO
        amp = 0
        if self._default_validation(tag, DETAL_TAG):
            amp += 1
        self._update_lists(DETAL_TAG, amp)
        return amp

    def _identify_as_timestamp(self, tag):
        # TODO
        amp = 0
        if self._default_validation(tag, TIMES_TAG):
            amp += 1
        self._update_lists(TIMES_TAG, amp)
        return amp

    # HELPERS:
    def _update_lists(self, info_type, amp):
        if amp:
            self.guesses[info_type] = amp
            self.tag_types.append(info_type)
            return True
        else:
            return False

    def _default_validation(self, tag, info_tag):
        return any([re.search(f, tag) for f in Identifier.info_types[info_tag]])
