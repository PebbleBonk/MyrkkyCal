'''
Created on 17.2.2017

@author: Olli Riikonen
'''
import pickle
from icalendar import Calendar
from bs4 import BeautifulSoup
import requests
import datetime
from geopy.geocoders import Nominatim, GoogleV3
from os import path
from urllib.request import urlopen
import params



def getGeoLocation(address):
    """ Returns a string containing the longitude and latitude
        of the address:
        @param address: a string containing the address
               for which to search the location
    """

    geolocator = GoogleV3()
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



def isNum(s):
    """ Checks if the string given as parameter is numeric
        @param s: a character to check if it is
               numeric or not
    """
    try:
        float(s)
        return True
    except ValueError:
        return False



def parseMyCoursesCalendar(icalendarFile, outputFileName):
    """ Edits MyCourses exported .ics calendar into nicer form

    Script takes the .ics file and edits the summary of each
    event. As MyCourses exported calendar events' summaries
    contain extra information in addition to the name of the
    event, it is split into respective fields supported by
    the icalendar format, such as location, URL and geo.

    The format of the summary and how to split it was deduced
    based on events exported for five courses so some variation
    and bugs (information in wrong field/ missing information)
    might be present in the created calendar.

    Args:
        icalendarFile: the calendar exported from MyCourse in
        icalendar format (.ics)

    Returns:
        Nothing

    """

    """ Open the icalendar file exported form MyCourses:"""
    """ Check if the given address is URL or path:"""
    try:
        data = urlopen(icalendarFile)
        print("URL")
    except:
        data = open(icalendarFile, "r", encoding='utf-8')
        print("Path")

    datas =data.read()
    cal = Calendar.from_ical(datas)


    """The current year to help check the URL of courses"""
    year = str(datetime.datetime.now().year)


    """ Dictionaries for the most resource demanding lookups
        also works as a safety measure as google doesn't like
        too frequent inquiries (weblist, searching the course
        web-page)"""

    """ Open tha saved website and geolocation datas: """
    geoList = pickle.load(open(params.GEO_LOC_SAVE_FILE, 'rb'))
    webList = pickle.load(open(params.WEBSITE_SAVE_FILE, 'rb'))
    # try:
    #     geoList = pickle.load(open(params.GEO_LOC_SAVE_FILE, 'rb'))
    # except:
    #     geoList = {}
    # try:
    #     webList = pickle.load(open(params.WEBSITE_SAVE_FILE, 'rb'))
    # except:
    #     webList = {}


    """ Go through the events and split the information
        to their respective fields: """
    for event in cal.walk('vevent'):

        description = event.get('description')
        summery = ','.join(event.get('summary').rsplit('(', 1))
        #summery = event.get('summary').replace("(", ",")
        tags = str(summery).split(sep=",")
        if len(tags) > 4:
            tags = tags[0:-1]

        if len(tags) == 2:
            """ Syntax for event with two data point:
            0. eventType nameFin/nameEng/nameSwe |
               eventName/ courseCode - courseName
            1. courseSchedule """
            tags = tags[0].split('/')

            if isNum(tags[0][2]):
                summary = tags[1]
            else:
                summary = tags[0]

            courseName = tags[-1].split('-')[-1].strip()
            courseCode = '-'.join(tags[-1].split('-')[0:-1]).strip()
            summary = ', '.join([summary, courseName])

        elif len(tags) == 4:
            """ Syntax for event with four data points:
                0. eventType nameFin/nameEng/nameSwe,
                1. location(room name) / location(room code) |
                    location(room code) (location(room code))
                2. location(address)/ courseCode - courseName
                3. courseSchedule """
            eventType = tags[0].split('/')[1]
            courseName = tags[-1].split('-')[-1].strip()
            summary = ', '.join([eventType, courseName])

            courseCode = '-'.join(tags[-1].split('/')[-1].\
                                           split('-')[0:2]).strip()

            room = tags[1].split('(')[0]
            address = tags[2]  #tags[-1].split('/')[0].strip()
            location = ' at '.join([room, address])

        # elif len(tags) == 4:
        #     """ Syntax for event with five data points:
        #         0. eventType nameFin/nameEng/nameSwe
        #         1. location(room name) / location(room code)
        #         2. location(building),
        #         3. location(address)/ courseCode - courseName
        #         4. courseSchedule """
        #     eventType = tags[0].split('/')[1]
        #     courseName = tags[-1].split('-')[-1].strip()
        #     summary = ', '.join([eventType, courseName])
        #
        #     courseCode = '-'.join(tags[-1].split('/')[-1].\
        #                                    split('-')[0:2]).strip()
        #
        #     room = tags[1].split('(')[0]
        #     building = tags[2]
        #     address = tags[-1].split('/')[0].strip()
        #     location = ', '.join([room, building, address])

        elif len(tags) == 5:
            """ Syntax for event with five data points:
                0. eventType nameFin/nameEng/nameSwe
                1. location(room name) / location(room code)
                2. location(building),
                3. location(address)/ courseCode - courseName
                4. courseSchedule """
            eventType = tags[0].split('/')[1]
            courseName = tags[-1].split('-')[-1].strip()
            summary = ', '.join([eventType, courseName])

            courseCode = '-'.join(tags[-1].split('/')[-1].\
                                           split('-')[0:2]).strip()

            room = tags[1].split('(')[0]
            building = tags[2]
            address = tags[3]  # tags[-1].split('/')[0].strip()
            location = ', '.join([room, building, address])

        else:
            print("Couldn't parse: "+str(len(tags)))
            print(tags)
            continue

        """ Find the web page of the course with google search
            as MyCourses API is not openly available:"""
        if courseCode not in webList.keys():
            webPage = findCourseWeppage('+'.join([courseCode,year]))
            print(webPage)
            if "mycourses" in webPage:
                webList[courseCode] = webPage
        else:
            webPage = webList[courseCode]

        description = ''.join(["Course code: ",courseCode, "\n",
                               "Course URL: ", webPage, "\n",
                               description])

        """ Find the geological location of the event: """
        if address not in geoList.keys():
            if address != "":
                geo = getGeoLocation(address)
                print(geo)
                geoList[address] = geo
            else:
                geo = ""
        else:
            geo = geoList[address]


        """ ''' Testing the program with basic printing:'''
        print("Summary:", summary)
        print("Location:", location)
        print("Description:", description )
        print("Geo:", geo)
        print()
        """

        # print("PARSED: "+str(len(tags)))
        # print(tags)
        # print("summary:"+summary+" descr: "+description+" loc "+location)
        event['summary'] = summary.replace("...)", "")
        event['description'] = description
        event['location'] = location
        event['geo'] = geo
        event['url'] = webPage

    outputFile = open(outputFileName, 'wb')
    outputFile.write(cal.to_ical())
    outputFile.close()

    # TODO: save geolocations
    pickle.dump(geoList, open(params.GEO_LOC_SAVE_FILE, 'wb'))
    # TODO: Save websites:
    print(webList)
    pickle.dump(webList, open(params.WEBSITE_SAVE_FILE, 'wb'))


''' Possible data in indexes:

    0     eventType nameFin/nameEng/nameSwe/ courseCode - courseName | eventName/ courseCode - courseName
    1     location(room name) / location(room code) | location(room code) (location(room code)) | courseSchedule
    2 - | location(building) | location(building)/ courseCode - courseName
    3 - | location(address)/ courseCode - courseName | courseSchedule
    4 - | courseSchedule

    --

    Possible data collections:
    length
    1 -

    2 eventType nameFin/nameEng/nameSwe | eventName/ courseCode - courseName, ...
      courseSchedule

    3 -

    4 eventType nameFin/nameEng/nameSwe , location(room name) / location(room code) ...
      location(room code) (location(room code)), location(address)/ courseCode - courseName, ...
      courseSchedule

    5 eventType nameFin/nameEng/nameSwe , location(room name) / location(room code), ...
      location(building), location(address)/ courseCode - courseName, courseSchedule


'''



if __name__ == '__main__':

    icalFile = path.join(params.ROOT_DIR, "icalexport.ics")
    icalURL = params.ICAL_URL

    outputFileName = path.join(params.ROOT_DIR, params.SAVE_FILE_NAME)

    parseMyCoursesCalendar(icalURL, outputFileName)
    # parseMyCoursesCalendar(icalFile, outputFileName)
