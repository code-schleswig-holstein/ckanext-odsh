import ckan.lib.base as base
from ckan.controllers.home import HomeController
from ckan.controllers.user import UserController
from ckan.controllers.api import ApiController
from ckan.controllers.feed import FeedController
from ckan.controllers.package import PackageController
import ckan.lib.helpers as h
import ckan.authz as authz
from ckan.common import c
import logging
import matomo 
import ckan.logic as logic

abort = base.abort
log = logging.getLogger(__name__)

class OdshRouteController(HomeController):
    def info_page(self):
        h.redirect_to('http://www.schleswig-holstein.de/odpinfo')
    def start(self):
        h.redirect_to('http://www.schleswig-holstein.de/odpstart')
    def not_found(self):
        abort(404)

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

    def dashboard_datasets(self):
        if not authz.is_sysadmin(c.user):
            abort(404)
        return super(OdshUserController,self).dashboard_datasets(id)

    def read(self, id=None):
        return super(OdshUserController,self).read(id)

    def follow(self, id):
        if not authz.is_sysadmin(c.user):
            abort(404)
        return super(OdshUserController,self).follow(id)

    def unfollow(self, id):
        if not authz.is_sysadmin(c.user):
            abort(404)
        return super(OdshUserController,self).unfollow(id)

    def activity(self, id, offset=0):
        if not authz.is_sysadmin(c.user):
            abort(404)
        return super(OdshUserController,self).activity(id, offset)

class OdshPackageController(PackageController):
    pass

class MamotoApiController(ApiController):

    def _post_matomo(self, user, request_obj_type, request_function, request_id):
    # if config.get('googleanalytics.id'):
        data_dict = {
            "siteid": 1,
            "rec": 1,
            # "tid": config.get('googleanalytics.id'),
            # "cid": hashlib.md5(user).hexdigest(),
            # # customer id should be obfuscated
            # "t": "event",
            # "dh": c.environ['HTTP_HOST'],
            # "dp": c.environ['PATH_INFO'],
            # "dr": c.environ.get('HTTP_REFERER', ''),
            # "ec": "CKAN API Request",
            # "ea": request_obj_type+request_function,
            # "el": request_id,
        }
        # plugin.GoogleAnalyticsPlugin.analytics_queue.put(data_dict)

    def action(self, logic_function, ver=None):
        try:
            function = logic.get_action(logic_function)
            side_effect_free = getattr(function, 'side_effect_free', False)
            request_data = self._get_request_data(
                try_url_params=side_effect_free)
            if isinstance(request_data, dict):
                id = request_data.get('id', '')
                if 'q' in request_data:
                    id = request_data['q']
                if 'query' in request_data:
                    id = request_data['query']
                # self._post_matomo(c.user, logic_function, '', id)
                userid=hashlib.md5(user).hexdigest()
                matomo.create_matomo_request(userid)
        except Exception, e:
            log.debug(e)
            pass
        

        return ApiController.action(self, logic_function, ver)


    # def list(self, ver=None, register=None, subregister=None, id=None):

    # def show(self, ver=None, register=None, subregister=None,
            #  id=None, id2=None):
        # self._post_analytics(c.user,
        #                      register +
        #                      ("_"+str(subregister) if subregister else ""),
        #                      "show",
        #                      id)
        # return ApiController.show(self, ver, register, subregister, id, id2)

    # def create(self, ver=None, register=None, subregister=None,
    #            id=None, id2=None):


    # def update(self, ver=None, register=None, subregister=None,
    #            id=None, id2=None):

    # def delete(self, ver=None, register=None, subregister=None,
    #            id=None, id2=None):

    # def search(self, ver=None, register=None):

class MatomoFeedController(FeedController):
    def custom(self):
        matomo.create_matomo_request()
        return FeedController.custom(self)