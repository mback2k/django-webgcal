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

    def __iter__(self):
        return iter(self.cals)

class vCalendar(object):
    def __init__(self, soup):
        self.soup = soup
        self.events = map(vEvent, self.soup.findAll(attrs='vevent'))

    def __iter__(self):
        return iter(self.events)

class vEvent(object):
    def __init__(self, soup):
        self.soup = soup

    def __getattr__(self, attr):
        return self.getContent(attr)

    def dt(self, attr):
        return self.getDatetime(attr)

    def getDatetime(self, attr):
        return parse(self.getContent(attr))

    def getContent(self, attr):
        soup = self.soup.find(attrs=attr)
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
        return content

    def _getContent(self, soup):
        if soup.string:
            return str(soup.string).decode('utf-8').strip().strip('"')
        contents = []
        for elem in soup.contents:
            contents.append(self._getContent(elem))
        if not contents:
            return ''
        return max(contents, key=len)
