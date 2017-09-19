#! -*- coding utf-8 -*-
import datetime
import pickle
import sys
import re

from urllib.request import urlopen
from os import path

from icalendar import Calendar
from bs4 import BeautifulSoup
import requests

import params
from identifier import Identifier


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


class MyCoursesParser(object):
    """ Parse a calendar event summary for information

    Tries to analyse given string and compare it to
    syntaxes to parse information.

    Based hgeavily on self analysed course Syntax,
    thus improvement heavily suggested. """

    # "course_code": [r'[A-Z]+-[A-Z]\d+',  # ELEC
    #                 r'\d{2}[A-Z]\d{5}',  # Business
    #                 r'[A-Za-z]+-\d+.\d+']  # Languages


    # info_types = {CLSRM_TAG: [r'([A-Z]*\d+-*\d+[a-z]*) \(\1\)',
    #                           r'[\w-]+ / \w+',
    #                           r'[^-][A-Z]\d{3}'],

    #               ADDRS_TAG: [r'[\w-]+ \d{1,3} ?[A-Za-z]?'],
    #               EVENT_TAG: [r'([A-Z]\d{2}|[A-Z]{2}\d)[\w ]*/[\w ]*/[\w ]*'],
    #               DETAL_TAG: [r'[A-Z]+-[\d\w]+ - [\w ]+'],
    #               TIMES_TAG: [r'\d{1,2}\.\d{1,2}\.\d{2,4}']}

    def __init__(self, lang='en'):
        self.geo = (None, None)
        self.description = ""
        self.summary = ""
        self.lang = lang
        self.url = ""
        self.infos = {BLDNG_TAG: None,
                      ADDRS_TAG: None,
                      CLSRM_TAG: None,
                      CCODE_TAG: None,
                      CNAME_TAG: None,
                      EVENT_TAG: None,
                      DETAL_TAG: None,
                      ERROR_TAG: None,
                      SUMMR_TAG: None,
                      LOCAT_TAG: None,
                      TIMES_TAG: None}

    def parse(self, string):
        tags = string.split(params.INFO_SEPARATOR)
        tag_types = {}

        if len(tags) == 1:
            self.infos[ERROR_TAG] = self.tag_type(tags[0])
            return

        # Identify info class for each tag:
        for tag in tags:
            identifier = Identifier()
            tag_types[tag] = identifier.identify_tag_type(tag)
        # for tag in tags:
        #     tag_types[tag] = self.tag_type(tag)

        for tag, types in tag_types.items():
            if len(types) == 1:
                self.infos[types[0]] = tag.strip()

        # Parse info into nicer, more readable shape:
        try:
            self._parse_course_details()
            self._parse_event_type()
            self._parse_classroom()
            self._parse_timestamp()
            self._parse_building()
            self._parse_location()
            self._parse_summary()
        except:
            ## For tesing:
            print("ERROR PARSING:")
            print(tags)
            e = sys.exc_info()[0]
            for k, v in self.infos.items():
                print(k,':', v)
            a = input("Press enter to continue - " + 
                      "write input to raise error\n")
            if len(a):
                raise e
            print()

        for k, v in self.infos.items():
            print(k,':', v)
        a = input("Press enter to continue\n")

    # def tag_type(self, tag):
    #     tag_types = []
    #     info_types = MyCoursesParser.info_types
    #     for infotype in info_types:
    #         if any([re.search(f, tag) for f in info_types[infotype]]):
    #             tag_types.append(infotype)
    #     if len(tag_types) == 0 and not hasNumbers(tag) and len(tag) < params.BLDNG_TH:
    #         tag_types.append(BLDNG_TAG)
    #     if len(tag_types) == 0 and not hasNumbers(tag):
    #         tag_types.append(EVENT_TAG)

    #     return tag_types

    def _parse_course_details(self):
        if self.infos[DETAL_TAG] is None or \
           ' - ' not in self.infos[DETAL_TAG]:
            return False

        parts = self.infos[DETAL_TAG].replace("...)", '').split(" - ")
        self.infos[CNAME_TAG] = parts[1]
        self.infos[CCODE_TAG] = parts[0]
        return True

    def _parse_event_type(self):
        event_tag = self.infos[EVENT_TAG]
        # Assert:
        if event_tag is None:
            return False
        # Standard format:
        if '/' in event_tag:
            lang_choices = re.sub(r'[A-Z]\d{2} ', '', event_tag)
            lang_choices = lang_choices.split('/')
            event_tag = lang_choices[params.LANG_IDX[self.lang]]
        # Parenthesis format:
        elif re.search(r'\(.*\)', event_tag):
            event_tag = re.search(r'\(.*\)', event_tag).group(0)
            event_tag = event_tag.strip('()')
        self.infos[EVENT_TAG] = event_tag
        return True

    def _parse_classroom(self):
        if self.infos[CLSRM_TAG] is None:
            return False
        self.infos[CLSRM_TAG] = re.sub(r'\(.*\)', '', self.infos[CLSRM_TAG])
        return True

    def _parse_summary(self):
        if self.infos[EVENT_TAG] is None:
            self._parse_event_type()
        if self.infos[DETAL_TAG] is None:
            self._parse_course_details()
        self.infos[SUMMR_TAG] = ', '.join([self.infos[EVENT_TAG],
                                           self.infos[CNAME_TAG]])
        return True

    def _parse_timestamp(self):
        if self.infos[TIMES_TAG] is None:
            return False
        self.infos[TIMES_TAG] = self.infos[TIMES_TAG].replace('...)', '')
        return True

    def _parse_building(self):
        a = self.infos[ADDRS_TAG]
        b = self.infos[BLDNG_TAG]
        b = params.BUILDINGS[a] if not b and a in params.BUILDINGS else None
        self.infos[BLDNG_TAG] = b

    def _parse_location(self):
        a = '' if self.infos[ADDRS_TAG] is None else self.infos[ADDRS_TAG]
        b = '' if self.infos[BLDNG_TAG] is None else self.infos[BLDNG_TAG]
        r = '' if self.infos[CLSRM_TAG] is None else self.infos[CLSRM_TAG]
        location = ', '.join([l for l in [a, b, r] if l])
        if not location:
            return False
        self.infos[LOCAT_TAG] = location
        return True


class MyCoursesParser_ELEC(MyCoursesParser):
    """ A parser specifically for courses in ELEC """
    pass
