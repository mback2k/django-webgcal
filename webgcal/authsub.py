from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
import gdata.calendar.service
import gdata.alt.appengine
import gdata.service
import gdata.auth

class MainPage(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        calendar_service = gdata.calendar.service.CalendarService()
        gdata.alt.appengine.run_on_appengine(calendar_service)
                                     
        session_token = None
        auth_token = gdata.auth.extract_auth_sub_token_from_url(self.request.url)
        
        if auth_token:
            session_token = calendar_service.upgrade_to_session_token(auth_token)
        if session_token:
            calendar_service.token_store.add_token(session_token) 
            
        try:
            calendar_service.AuthSubTokenInfo()
        except gdata.service.RequestError:
            self.redirect('/')
        else:
            self.redirect('/dashboard/')

def main():
    application = webapp.WSGIApplication([('/authsub/', MainPage)], debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()