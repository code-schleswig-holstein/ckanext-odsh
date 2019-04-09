import ckan.lib.base as base
from ckan.controllers.home import HomeController
from ckan.controllers.user import UserController
from ckan.controllers.api import ApiController
from ckan.controllers.feed import FeedController
from ckan.controllers.package import PackageController
from ckan.controllers.feed import FeedController, ITEMS_LIMIT, _package_search, _create_atom_id
import ckan.lib.helpers as h
import ckan.authz as authz
from ckan.common import c
import logging
import matomo 
import ckan.logic as logic
from ckan.common import c, request, config
import hashlib
import ckan.plugins.toolkit as toolkit
from ckanext.dcat.controllers import DCATController
from ckan.lib.search.common import (
    make_connection, SearchError, SearchQueryError
)
import pysolr

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
        if not c.user:
            h.redirect_to(controller='user', action='login')
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


class OdshApiController(ApiController):
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
                userid=None
                if c.user:
                    userid=hashlib.md5(c.user).hexdigest()[:16]
                matomo.create_matomo_request(userid)
            else:
                matomo.create_matomo_request()

        except Exception, e:
            log.error(e)
        
        return ApiController.action(self, logic_function, ver)


class OdshDCATController(DCATController):
    def read_catalog(self, _format):
        matomo.create_matomo_request()
        return DCATController.read_catalog(self,_format)


class OdshFeedController(FeedController):
    def custom(self):
        matomo.create_matomo_request()
        extra_fields=['ext_startdate', 'ext_enddate', 'ext_bbox', 'ext_prev_extent']
        q = request.params.get('q', u'')
        fq = ''
        search_params = {}
        extras = {}
        for (param, value) in request.params.items():
            if param not in ['q', 'page', 'sort'] + extra_fields \
                    and len(value) and not param.startswith('_'):
                search_params[param] = value
                fq += ' %s:"%s"' % (param, value)
            if param in extra_fields:
                extras[param]=value
        search_params['extras']=extras

        page = h.get_page_number(request.params)

        limit = ITEMS_LIMIT
        data_dict = {
            'q': q,
            'fq': fq,
            'start': (page - 1) * limit,
            'rows': limit,
            'sort': request.params.get('sort', None),
            'extras': extras
        }

        item_count, results = _package_search(data_dict)

        navigation_urls = self._navigation_urls(request.params,
                                                item_count=item_count,
                                                limit=data_dict['rows'],
                                                controller='feed',
                                                action='custom')

        feed_url = self._feed_url(request.params,
                                  controller='feed',
                                  action='custom')

        atom_url = h._url_with_params('/feeds/custom.atom',
                                      search_params.items())

        alternate_url = self._alternate_url(request.params)

        site_title = config.get('ckan.site_title', 'CKAN')

        return self.output_feed(results,
                                feed_title=u'%s - Custom query' % site_title,
                                feed_description=u'Recently created or updated'
                                ' datasets on %s. Custom query: \'%s\'' %
                                (site_title, q),
                                feed_link=alternate_url,
                                feed_guid=_create_atom_id(atom_url),
                                feed_url=feed_url,
                                navigation_urls=navigation_urls)


class OdshAutocompleteController(ApiController):
    def autocomplete(self, q):
        query = {
            'spellcheck.q': q,
            'wt': 'json'}

        conn = make_connection(decode_dates=False)
        log.debug('Suggest query: %r' % query)
        try:
            solr_response = conn.search('', search_handler='suggest', **query)
        except pysolr.SolrError as e:
            raise SearchError('SOLR returned an error running query: %r Error: %r' %
                              (query, e))

        suggest = solr_response.raw_response.get('spellcheck')
        return base.response.body_file.write(str(suggest))
