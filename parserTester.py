from icalendar import Calendar
from bs4 import BeautifulSoup
import requests
import datetime
from os import path
from urllib.request import urlopen
import params
from MCparser import MyCoursesParser
import pickle
import sys
from geopy.geocoders import Nominatim, GoogleV3


def getGeoLocation(address):
    """ Returns a string containing the longitude and latitude
        of the address:
        @param address: a string containing the address
               for which to search the location
    """
    return ""
    # geolocator = GoogleV3()
    geolocator = Nominatim()
    location = geolocator.geocode(address)
    #print(location.address)
    if location:
        return ';'.join([str(location.latitude), \
                         str(location.longitude)])
    else:
        return ""


def findCourseWeppage(key):
    """ Returns a string containing the URL address
        of the first search result from Google for
        the search term given in parameter key
        @param key: a string containing the search
               term for which the "I'm feeling lucky"
               search is performed
    """

    tries, max_tries = 0, 3

    while tries < max_tries:
        goog_search = "https://www.google.fi/search?rls=en&q=" + \
                       key + "&ie=UTF-8&oe=UTF-8"

        r = requests.get(goog_search)
        soup = BeautifulSoup(r.text, "html.parser")
        if "mycourses" in soup.find('cite').text:
            return soup.find('cite').text
        tries += 1
    return "https://bit.ly/myrkky"


def getLocation(address):
    try:
        geoList = pickle.load(open(params.GEO_LOC_SAVE_FILE, 'rb'))
    except:
        geoList = {}

    if address not in geoList.keys():
        if address != "":
            geo = getGeoLocation(address)
            geoList[address] = geo
        else:
            geo = ""
    else:
        geo = geoList[address]

    pickle.dump(geoList, open(params.GEO_LOC_SAVE_FILE, 'wb'))
    return geo


def form_description(courseCode, description):
    """ Find the web page of the course with google search
        as MyCourses API is not openly available:"""
    try:
        webList = pickle.load(open(params.WEBSITE_SAVE_FILE, 'rb'))
    except:
        webList = {}

    # The current year to help check the URL of courses
    year = str(datetime.datetime.now().year)

    if courseCode not in webList.keys():
        webPage = findCourseWeppage('+'.join([courseCode,year]))
        # Simple validation for saving:
        if "mycourses" in webPage:
            webList[courseCode] = webPage
    else:
        webPage = webList[courseCode]

    pickle.dump(webList, open(params.WEBSITE_SAVE_FILE, 'wb'))

    description = ''.join(["Course code: ",courseCode, "\n",
                           "Course URL: ", webPage, "\n",
                           description])
    return description, webPage


def test_parser(icalendarFile, outputFileName):
    try:
        data = urlopen(icalendarFile)
        print("URL")
    except:
        data = open(icalendarFile, "r", encoding='utf-8')
        print("Path")

    datas = data.read()
    cal = Calendar.from_ical(datas)

    """ Go through the events and parse the information: """
    for event in cal.walk('vevent'):
        event_info = ','.join(event.get('summary').rsplit('(', 1))
        parser = MyCoursesParser()
        parser.parse(event_info)

        if parser.infos["errors"] is not None:
            continue

        summary = parser.infos["summary"]
        course_code = parser.infos["course_code"]
        location = parser.infos["location"]
        address = parser.infos["address"]
        descr = event.get('description')

        description, webPage = form_description(course_code, descr)
        geo = getLocation(address)

        event['summary'] = summary
        event['description'] = description
        event['location'] = location
        event['geo'] = geo
        event['url'] = webPage

    outputFile = open(outputFileName, 'wb')
    outputFile.write(cal.to_ical())
    outputFile.close()

if __name__ == '__main__':

    if len(sys.argv) == 2:
        icalfilename = sys.argv[1]
    else:
        icalfilename = "icalexport-4.ics"

    icalFile = path.join(params.IN_DIR, icalfilename)
    # icalURL = params.ICAL_URL

    outputFileName = path.join(params.OUT_DIR, "edited_"+icalfilename)

    test_parser(icalFile, outputFileName)
