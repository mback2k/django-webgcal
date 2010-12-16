from hcalendar import hCalendar
import urllib2

def parsePage(url):
    req = urllib2.Request(url, None, {'User-agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'})
    fp = urllib2.urlopen(req)
    html = fp.read()
    for cal in hCalendar(html):
        for event in cal:
            print event.dt('dtstart'), event.summary

parsePage('http://en.wikipedia.org/wiki/List_of_House_episodes')
parsePage('http://en.wikipedia.org/wiki/List_of_NCIS_episodes')
parsePage('http://en.wikipedia.org/wiki/List_of_Fringe_episodes')
parsePage('http://en.wikipedia.org/wiki/List_of_Scrubs_episodes')
