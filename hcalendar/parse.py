from hcalendar import hCalendar
import urllib2

def parsePage(url):
    print '-'*79
    print url
    file = urllib2.urlopen(urllib2.Request(url, headers={'User-agent': 'WebGCal'}))
    hcal = hCalendar(file)
    for cal in hcal:
        for event in cal:
            print '-'*79
            for attr in dir(event):
                print '%s: %s' % (attr, repr(getattr(event, attr)))

parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar1.htm')
parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar2.htm')
parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar3.htm')

parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar4.htm')
parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar5.htm')

parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar6.htm')
parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar7.htm')

parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar8.htm')
parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar9.htm')

parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar10.htm')
parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar11.htm')

parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar12.htm')
parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar13.htm')

parsePage('http://ufxtract.com/testsuite/hcalendar/hcalendar14.htm')

parsePage('http://microformats.org/wiki/hcalendar')

parsePage('http://en.wikipedia.org/wiki/List_of_House_episodes')
parsePage('http://en.wikipedia.org/wiki/List_of_NCIS_episodes')
parsePage('http://en.wikipedia.org/wiki/List_of_Fringe_episodes')
parsePage('http://en.wikipedia.org/wiki/List_of_Scrubs_episodes')
