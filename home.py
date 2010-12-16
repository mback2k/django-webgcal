from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

class MainPage(webapp.RequestHandler):
    def get(self):
        self.response.out.write('Hello, webapp World!<br />')
        self.response.out.write('<a href="/authsub/">Login and connect</a>')

def main():
    application = webapp.WSGIApplication([('/', MainPage)], debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()