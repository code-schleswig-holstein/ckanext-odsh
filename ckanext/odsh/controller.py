import ckan.lib.base as base
from ckan.controllers.home import HomeController

class OdshRouteController(HomeController):
    def info_page(self):
        return base.render('info_page.html')