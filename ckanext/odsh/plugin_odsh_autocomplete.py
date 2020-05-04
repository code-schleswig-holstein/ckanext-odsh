import ckan.plugins as plugins
import ckanext.odsh.logic.action as action

class OdshAutocompletePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IActions)

    def get_actions(self):
        return {'autocomplete': action.autocomplete}