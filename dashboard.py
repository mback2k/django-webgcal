from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import gdata.calendar.service
import gdata.alt.appengine
import gdata.auth

class MainPage(webapp.RequestHandler):
    def get(self):
        calendar_service = gdata.calendar.service.CalendarService()
        gdata.alt.appengine.run_on_appengine(calendar_service)
                                     
        try:
            calendar_service.AuthSubTokenInfo()
        except (gdata.service.NonAuthSubToken, gdata.service.RequestError):
            return self.redirect(str(calendar_service.GenerateAuthSubURL('http://localhost:8080/authsub/', ('http://www.google.com/calendar/feeds/', 'https://www.google.com/calendar/feeds/'), secure=False, session=True)))
        
        feed = None    
        try:
            feed = calendar_service.GetOwnCalendarsFeed()
        except:
            return self.redirect(str(calendar_service.GenerateAuthSubURL('http://localhost:8080/authsub/', ('http://www.google.com/calendar/feeds/', 'https://www.google.com/calendar/feeds/'), secure=False, session=True)))
            
        self.response.out.write(feed.title.text)
        for i, a_calendar in enumerate(feed.entry):
            self.response.out.write('\t%s. %s' % (i, a_calendar.title.text,))

def main():
    application = webapp.WSGIApplication([('/dashboard/', MainPage)], debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()