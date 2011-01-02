from BeautifulSoup import BeautifulSoup
from dateutil.parser import parse

class hCalendar(object):
    def __init__(self, html):
        self.soup = BeautifulSoup(html)
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
    def __init__(self, soup):
        self.soup = soup
        self.content = {}
        self.datetime = {}
        
    def __str__(self):
        return str(self.soup)

    def __getattr__(self, attr):
        if attr in ['dtstart', 'dtend', 'dtstamp', 'last_modified']:
            return self.getDatetime(attr.replace('_', '-'))
        elif attr in ['duration', 'summary', 'uid', 'method', 'category', 'url', 'description', 'status', 'class']:
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
                elif elem.name in ['img', 'area']:
                    content += elem['alt']
                else:
                    content += self._getContent(elem)
            self.content[attr] = content
        return self.content[attr]

    def _getContent(self, soup):
        if soup.string:
            return str(soup.string).decode('utf-8').strip().strip('"')
        contents = []
        for elem in soup.contents:
            contents.append(self._getContent(elem))
        if not contents:
            return ''
        return max(contents, key=len)
