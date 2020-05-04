import datetime

import ckanext.odsh.plugin as plugin

class TestMethodBeforeView(object):
    date_time_format = '%Y-%m-%dT%H:%M:%S'

    def test_before_view_adds_false_for_old_dataset(self):
        plugin_object = plugin.OdshPlugin()
        today = datetime.date.today()
        hundred_days_ago = today - datetime.timedelta(days=100)
        hundred_days_ago_as_ckan_str = self._date_as_ckan_str(hundred_days_ago)
        dict_for_template = plugin_object.before_view(
            {
                u'extras': [
                    {u'key': 'issued', u'value': hundred_days_ago_as_ckan_str}
                ]
            }
        )
        assert dict_for_template['is_new']==False

    def _date_as_ckan_str(self, date):
        return date.strftime(self.date_time_format)

    def test_before_view_adds_true_for_new_dataset(self):
        plugin_object = plugin.OdshPlugin()
        today = datetime.date.today()
        ten_days_ago = today - datetime.timedelta(days=10)
        ten_days_ago_as_ckan_str = self._date_as_ckan_str(ten_days_ago)
        dict_for_template = plugin_object.before_view(
            {
                u'extras': [
                    {u'key': 'issued', u'value': ten_days_ago_as_ckan_str}
                ]
            }
        )
        assert dict_for_template['is_new']==True
    
    def test_before_view_does_not_modify_unconcerned_dict_values(self):
        plugin_object = plugin.OdshPlugin()
        today = datetime.date.today()
        ten_days_ago = today - datetime.timedelta(days=10)
        ten_days_ago_as_ckan_str = self._date_as_ckan_str(ten_days_ago)
        dict_for_template = plugin_object.before_view(
            {
                u'extras': [
                    {u'key': 'issued', u'value': ten_days_ago_as_ckan_str}
                ],
                'some_other_key': 'some_other_value', 
            }
        )
        assert dict_for_template['some_other_key']=='some_other_value'