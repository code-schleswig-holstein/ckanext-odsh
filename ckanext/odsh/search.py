import ckanext.odsh.helpers as odsh_helpers

def before_search(search_params):
    _update_facet_mincount(search_params)
    _update_daterange_query(search_params)
    return search_params

def _update_facet_mincount(search_params):
    search_params.update({'facet.mincount': 0})

def _update_daterange_query(search_params):
    start_date, end_date = _get_start_and_end_date(search_params)
    is_no_range = not start_date and not end_date
    if is_no_range:
        return search_params
    start_date_or_star = start_date or '*'
    end_date_or_star = end_date or '*'
    start_query, end_query = _get_start_and_end_query(start_date_or_star, end_date_or_star)
    is_enclosing_range = start_date and end_date and start_date < end_date
    if is_enclosing_range:
        enclosing_query = _get_enclosing_query(start_date_or_star, end_date_or_star)
    else:
        enclosing_query = ''
    open_end_query = _get_open_end_query(end_date_or_star)
    fq_preset = search_params.get('fq')
    fq = _combine_query(fq_preset, start_query, end_query, enclosing_query, open_end_query)
    search_params.update({'fq': fq})

def _get_start_and_end_date(search_params):
    extras = search_params.get('extras')
    start_date_local, end_date_local = (
        extras.get(key)
        for key in ('ext_startdate', 'ext_enddate')
    )
    try:
        start_date, end_date = (
            odsh_helpers.extend_search_convert_local_to_utc_timestamp(date)
            for date in (start_date_local, end_date_local)
        )
    except ValueError:
        start_date = end_date = None
    return start_date, end_date

def _get_start_and_end_query(start_date, end_date):
    start_query, end_query = (
        '+extras_temporal_{start_or_end}:[{start_date} TO {end_date}]'.format(
            start_or_end=__,
            start_date=start_date,
            end_date=end_date
        )
        for __ in ('start', 'end')
    )
    return start_query, end_query

def _get_open_end_query(end_date):
    if end_date is '*':
        open_end_query = '(*:* NOT extras_temporal_end:[* TO *])'
    else:
        open_end_query = '((*:* NOT extras_temporal_end:[* TO *]) AND extras_temporal_start:[* TO {end_date}])'.format(
            end_date=end_date)
    return open_end_query

def _get_enclosing_query(start_date, end_date):
    enclosing_query_start = 'extras_temporal_start:[* TO {start_date}]'.format(
        start_date=start_date)
    enclosing_query_end = 'extras_temporal_end:[{end_date} TO *]'.format(
        end_date=end_date)
    enclosing_query = ' OR ({enclosing_query_start} AND {enclosing_query_end})'.format(
        enclosing_query_start=enclosing_query_start, enclosing_query_end=enclosing_query_end)
    return enclosing_query

def _combine_query(fq_preset, start_query, end_query, enclosing_query, open_end_query):
    combined_query = u'{fq_preset} ({start_query} OR {end_query} {enclosing_query} OR {open_end_query})'.format(
        fq_preset=fq_preset, 
        start_query=start_query, 
        end_query=end_query, 
        enclosing_query=enclosing_query, 
        open_end_query=open_end_query
    )
    return combined_query