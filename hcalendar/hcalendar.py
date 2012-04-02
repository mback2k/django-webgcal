import re, bs4, isodate, datetime

class hCalendar(object):
    def __init__(self, markup):
        self._soup = bs4.BeautifulSoup(markup)
        self._cals = self._soup.findAll(attrs='vcalendar')
        if self._cals:
            self._cals = map(vCalendar, self._cals)
        else:
            self._cals = [vCalendar(self._soup)]

    def __len__(self):
        return len(self._cals)

    def __iter__(self):
        return iter(self._cals)

    def __getitem__(self, key):
        return self._cals[key]

    def getCalendar(self):
        return self._cals

class vCalendar(object):
    def __init__(self, soup):
        self._soup = soup
        self.events = map(vEvent, self._soup.findAll(attrs='vevent'))

    def __str__(self):
        return str(self._soup)

    def __len__(self):
        return len(self.events)

    def __iter__(self):
        return iter(self.events)

    def __getitem__(self, key):
        return self.events[key]

    def getEvents(self):
        return self.events

class vEvent(object):
    ATTR_CONTENT  = ('summary', 'description', 'location', 'category', 'status', 'method', 'uid', 'url')
    ATTR_DATETIME = ('dtstart', 'dtend', 'dtstamp')
    ATTR_DURATION = ('duration',)
    ATTR_RELATION = {'duration': 'dtstart'}
    ATTR_FALLBACK = {'dtend': 'duration'}

    REGEX_DATE = re.compile(r'P(\d{4})-(\d{2})-(\d{2})')
    REGEX_DATETIME = re.compile(r'P(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})')

    def __init__(self, soup):
        self._soup = soup
        self._content = {}
        self._datetime = {}
        self._duration = {}
        
    def __str__(self):
        return str(self._soup)
        
    def __dir__(self):
        return list(self.ATTR_CONTENT + self.ATTR_DATETIME)
        
    def __getattr__(self, attr):
        if attr in self.ATTR_DATETIME:
            value = self.getDatetime(attr.replace('_', '-'))
        elif attr in self.ATTR_DURATION:
            value = self.getDuration(attr.replace('_', '-'))
        elif attr in self.ATTR_CONTENT:
            value = self.getContent(attr)
        if not value and attr in self.ATTR_FALLBACK:
            value = getattr(self, self.ATTR_FALLBACK[attr])
        if not attr in list(self.ATTR_CONTENT + self.ATTR_DATETIME + self.ATTR_DURATION):
            raise AttributeError
        return value

    def getDatetime(self, attr):
        if not attr in self._datetime:
            content = self.getContent(attr)
            if content:
                if not 'T' in content:
                    value = isodate.parse_date(content)
                else:
                    value = isodate.parse_datetime(content)
                if isinstance(value, datetime.date):
                    self._datetime[attr] = datetime.datetime(value.year, value.month, value.day)
                else:
                    self._datetime[attr] = value
            else:
                self._datetime[attr] = None
        return self._datetime[attr]

    def getDuration(self, attr):
        if not attr in self._duration:
            content = self.getContent(attr)
            if content and attr in self.ATTR_RELATION:
                if self.REGEX_DATETIME.match(content):
                    content = self.REGEX_DATETIME.sub(r'P\1Y\2M\3DT\4H\5M\6S', content)
                elif self.REGEX_DATE.match(content):
                    content = self.REGEX_DATE.sub(r'P\1Y\2M\3D', content)
                relation = getattr(self, self.ATTR_RELATION[attr])
                value = isodate.parse_duration(content)
                if isinstance(value, isodate.duration.Duration):
                    self._duration[attr] = value.tdelta + relation + datetime.timedelta(days=365*value.years) + datetime.timedelta(days=30*value.months)
                else:
                    self._duration[attr] = value + relation
            else:
                self._duration[attr] = None
        return self._duration[attr]

    def getContent(self, attr):
        if not attr in self._content:
            soup = self._soup.find(attrs=attr)
            if not soup:
                return None
            subs = soup.findAll(attrs='value')
            soup = subs if subs else [soup]
            content = ''
            for elem in soup:
                if elem.name == 'a' and 'href' in elem.attrs:
                    content += elem['href']
                elif elem.name == 'abbr' and 'title' in elem.attrs:
                    content += elem['title']
                elif elem.name == 'time' and 'datetime' in elem.attrs:
                    content += elem['datetime']
                elif elem.name in ['img', 'area'] and 'alt' in elem.attrs:
                    content += elem['alt']
                else:
                    content += self._getContent(elem)
            self._content[attr] = content
        return self._content[attr]

    def _getContent(self, soup):
        if soup.string:
            return soup.string.strip().strip('"')
        contents = []
        for elem in soup.contents:
            contents.append(self._getContent(elem))
        if not contents:
            return ''
        return max(contents, key=len)
