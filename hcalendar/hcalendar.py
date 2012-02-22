from dateutil.parser import parse
from bs4 import BeautifulSoup

class hCalendar(object):
    def __init__(self, markup):
        self.soup = BeautifulSoup(markup)
        self.cals = self.soup.findAll(attrs='vcalendar')
        if self.cals:
            self.cals = map(vCalendar, self.cals)
        else:
            self.cals = [vCalendar(self.soup)]

    def __len__(self):
        return len(self.cals)

    def __iter__(self):
        return iter(self.cals)

    def __getitem__(self, key):
        return self.cals[key]

    def getCalendar(self):
        return self.cals

class vCalendar(object):
    def __init__(self, soup):
        self.soup = soup
        self.events = map(vEvent, self.soup.findAll(attrs='vevent'))

    def __str__(self):
        return str(self.soup)

    def __len__(self):
        return len(self.events)

    def __iter__(self):
        return iter(self.events)

    def __getitem__(self, key):
        return self.events[key]

    def getEvents(self):
        return self.events

class vEvent(object):
    ATTR_DATETIME = ('dtstart', 'dtend', 'dtstamp', 'last_modified')
    ATTR_CONTENT  = ('summary', 'description', 'location', 'category', 'status', 'duration', 'method', 'uid', 'url')

    def __init__(self, soup):
        self.soup = soup
        self.content = {}
        self.datetime = {}
        
    def __str__(self):
        return str(self.soup)
        
    def __dir__(self):
        return list(self.ATTR_CONTENT + self.ATTR_DATETIME)
        
    def __getattr__(self, attr):
        if attr in self.ATTR_DATETIME:
            return self.getDatetime(attr.replace('_', '-'))
        elif attr in self.ATTR_CONTENT:
            return self.getContent(attr)
        raise AttributeError

    def getDatetime(self, attr):
        if not attr in self.datetime:
            content = self.getContent(attr)
            if content:
                self.datetime[attr] = parse(content)
            else:
                self.datetime[attr] = None
        return self.datetime[attr]

    def getContent(self, attr):
        if not attr in self.content:
            soup = self.soup.find(attrs=attr)
            if not soup:
                return None
            subs = soup.findAll(attrs='value')
            soup = subs if subs else [soup]
            content = ''
            for elem in soup:
                if elem.name == 'abbr':
                    content += elem['title']
                elif elem.name == 'time':
                    content += elem['datetime']
                elif elem.name in ['img', 'area']:
                    content += elem['alt']
                else:
                    content += self._getContent(elem)
            self.content[attr] = content
        return self.content[attr]

    def _getContent(self, soup):
        if soup.string:
            return soup.string.strip().strip('"')
        contents = []
        for elem in soup.contents:
            contents.append(self._getContent(elem))
        if not contents:
            return ''
        return max(contents, key=len)
