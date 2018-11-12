import ckan.lib.base as base
from ckan.controllers.home import HomeController
from ckan.controllers.user import UserController
import ckan.lib.helpers as h
import ckan.authz as authz
from ckan.common import c

abort = base.abort

class OdshRouteController(HomeController):
    def info_page(self):
        return base.render('info_page.html')

class OdshUserController(UserController):
    def me(self, locale=None):
        if not c.user:
            h.redirect_to(locale=locale, controller='user', action='login',
                          id=None)
        user_ref = c.userobj.get_reference_preferred_for_uri()
        h.redirect_to(locale=locale, controller='package', action='search')

    def dashboard(self, id=None, offset=0):
        if not authz.is_sysadmin(c.user):
            abort(404)
        return super(OdshUserController,self).dashboard(id,offset)
