from django import template
from django.utils.encoding import smart_unicode
from django.utils import dateformat, translation
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse

def get_query_string(p, new_params=None, remove=None):
    """
    Add and remove query parameters. From `django.contrib.admin`.
    """
    if new_params is None: new_params = {}
    if remove is None: remove = []
    for r in remove:
        for k in p.keys():
            if k.startswith(r):
                del p[k]
    for k, v in new_params.items():
        if k in p and v is None:
            del p[k]
        elif v is not None:
            p[k] = v
    return mark_safe('?' + '&amp;'.join([u'%s=%s' % (k, v) for k, v in p.items()]).replace(' ', '%20'))
    
def string_to_dict(string):
    """
    Usage::
    
        {{ url|thumbnail:"width=10,height=20" }}
        {{ url|thumbnail:"width=10" }}
        {{ url|thumbnail:"height=20" }}
    """
    kwargs = {}
    if string:
        string = str(string)
        if ',' not in string:
            # ensure at least one ','
            string += ','
        for arg in string.split(','):
            arg = arg.strip()
            if arg == '': continue
            kw, val = arg.split('=', 1)
            kwargs[kw] = val
    return kwargs

def string_to_list(string):
    """
    Usage::
    
        {{ url|thumbnail:"width,height" }}
    """
    args = []
    if string:
        string = str(string)
        if ',' not in string:
            # ensure at least one ','
            string += ','
        for arg in string.split(','):
            arg = arg.strip()
            if arg == '': continue
            args.append(arg)
    return args

register = template.Library()

@register.inclusion_tag('_response.html', takes_context=True)
def query_string(context, add=None, remove=None):
    """
    Allows the addition and removal of query string parameters.
    
    _response.html is just {{ response }}

    Usage:
    http://www.url.com/{% query_string "param_to_add=value, param_to_add=value" "param_to_remove, params_to_remove" %}
    http://www.url.com/{% query_string "" "filter" %}filter={{new_filter}}
    http://www.url.com/{% query_string "sort=value" "sort" %}
    """
    # Written as an inclusion tag to simplify getting the context.
    add = string_to_dict(add)
    remove = string_to_list(remove)
    params = dict(context['request'].GET.items())
    response = get_query_string(params, add, remove)
    return {'response': response }

from votes.views import TERM_KEY, term_list, find_period, find_district
from votes.models import DistrictAssociation, County

@register.inclusion_tag('opt_list.html', takes_context=True)
def generate_option_list(context, option):
    opt_list = []
    source_url = None
    session = context['request'].session
    if option == 'term':
        if TERM_KEY in session:
            chosen_term = session[TERM_KEY]
        else:
            chosen_term = None
        for term in term_list:
            opt = {'name': term.display_name, 'value': term.name}
            if chosen_term and opt['value'] == chosen_term:
                opt['selected'] = True
            opt_list.append(opt)
        if 'selected' in opt_list[0]:
            opt_list[0]['selected'] = False
        list_type = 'link'
    elif option == 'district':
        (begin, end) = find_period(context['request'])
        chosen_district = find_district(context['request'], begin, end)

        opt = { 'name': _('All districts'), 'value': 'all' }
#        if not chosen_district:
#            opt['selected'] = True
        opt_list.append(opt)
        d_list = DistrictAssociation.objects.list_between(begin, end)
        for d in d_list:
            # Finnish mods
            short = canonize_district(d)
            opt = { 'name': short, 'value': d }
            if chosen_district and chosen_district == d:
                opt['selected'] = True
            opt_list.append(opt)
        list_type = 'link'
    elif option == 'county':
        list_type = 'combobox'
        source_url = reverse("votes.views.autocomplete_county")

    return {'options': opt_list, 'type': list_type, 'name': option,
            'source_url': source_url}

@register.filter("truncate_chars")
def truncate_chars(value, max_length):
    if len(value) <= max_length:
        return value

    truncd_val = value[:max_length]
    if value[max_length] != " ":
        rightmost_space = truncd_val.rfind(" ")
        if rightmost_space != -1:
            truncd_val = truncd_val[:rightmost_space]
    if not truncd_val.endswith("..."):
        return truncd_val + "..."
    else:
        return truncd_val

@register.filter("i18n_date")
def i18n_date(date, format_name):
    lang = translation.get_language()
    suffix = fmt = ''
    if format_name == 'long-month':
        if lang == 'fi':
            fmt = 'j. F'
            suffix = 'ta'
        elif lang == 'en':
            fmt = 'jS F'
    elif format_name == 'numeric':
        if lang == 'fi':
            fmt = 'j.n.Y'
        elif lang == 'en':
            fmt = 'j/n/Y'
    s = dateformat.format(date, fmt)
    return s + suffix

def strip_suffix(str, suffix):
    pos = str.rfind(suffix)
    return str[:pos if pos != -1 else None]

@register.filter
def canonize_district(district):
    return strip_suffix(strip_suffix(district, ' vaalipiiri'), ' maakunnan')
