#! -*- coding: utf-8 -*-
import os


ROOT_DIR = dir_path = os.path.dirname(os.path.realpath(__file__))

ICAL_URL = "https://mycourses.aalto.fi/calendar/export_execute.php?userid=8175&authtoken=ce516db4b5d8c5bcbefbd200a83268a0fe44e2e7&preset_what=all&preset_time=custom"

GEO_LOC_SAVE_FILE = os.path.join(ROOT_DIR, "geosave.p")
WEBSITE_SAVE_FILE = os.path.join(ROOT_DIR, "websave.p")

SAVE_FILE_NAME = 'testCdal.ics'

LANG_IDX = {"fi": 1,
            "en": 1,
            "se": 2}

BUILDINGS = {"Otakaari 1": "Päälafka",
             "Maarintie 7": "TUAS",
             "Maarintie 8": "T-talo",
             "Otakaari 5": "Sähkölafka"}

INFO_SEPARATOR = ','
BLDNG_TH = 8

EVENT_TYPE_KEYWORDS = ["lecture", "luento", "föreläsn",
					   "exercise", "övning", "harjoitu",
					   "midterm", "mellanför", "väliko",
					   "quiz", "testi"]