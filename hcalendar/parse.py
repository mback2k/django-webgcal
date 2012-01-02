from hcalendar import hCalendar
import urllib2

def parsePage(url):
    req = urllib2.Request(url, None, {'User-agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'})
    fp = urllib2.urlopen(req)
    html = fp.read()
    hcal = hCalendar(html)
    for cal in hcal:
        for event in cal:
            print '-'*79
            for attr in dir(event):
                print '%s: %s' % (attr, repr(getattr(event, attr)))

parsePage('http://microformats.org/wiki/hcalendar')

parsePage('http://en.wikipedia.org/wiki/List_of_House_episodes')
parsePage('http://en.wikipedia.org/wiki/List_of_NCIS_episodes')
parsePage('http://en.wikipedia.org/wiki/List_of_Fringe_episodes')
parsePage('http://en.wikipedia.org/wiki/List_of_Scrubs_episodes')
