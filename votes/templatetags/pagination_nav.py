import re
from django import template
from django.http import QueryDict


ADJACENT = 3
CAPS = 1
RE_URL = re.compile('(.*)1(.*)')
register = template.Library()


def page_separator(current, count, adjacent=ADJACENT, caps=CAPS):
    if current < adjacent + 1:
        adjacent += adjacent - current + 1
    elif count - current < adjacent:
        adjacent += adjacent - (count - current)
    bits = []
    if current > (1 + adjacent + caps):
        if caps:
            bits.append(range(1, caps+1))
        start = current - adjacent
    else:
        start = 1
    if current + adjacent < count - caps:
        end = current + adjacent
    else:
        end = count
    bits.append(range(start, end+1))
    if end != count:
        if caps:
            bits.append(range(count-caps+1, count+1))
    return bits


def get_page_context(page, url_func, adjacent, caps):
    if not page:
        return {}
    current = page.number
    count = page.paginator.num_pages
    if count < 2:
        return {}
    pages = []
    for page_group in page_separator(current, count, adjacent, caps):
        group = []
        for number in page_group:
            url = url_func(number)
            if not url:
                return {}
            group.append({'url': url, 'number': number,
                          'current': page.number==number})
        pages.append(group)
    c = {'pages': pages}
    if current > 1:
        c['previous_url'] = url_func(current-1)
    if current < count:
        c['next_url'] = url_func(current+1)
    return c


@register.inclusion_tag('pagination-nav.html')
def pagination_nav(page, url, first_page_url=None, adjacent=ADJACENT, caps=CAPS):
    """
    Generate Digg-like pagination navigation for URLs like "/entries/page/5/".

    Required arguments:

    page
        A ``django.core.paginator`` ``Page`` object
    url
        An example URL to navigate to page 1 (the last character ``"1"`` in the
        URL gets replaced with the actual page number)

    Optional arguments:

    first_page_url
        An alternate first page exact URL
    adjacent
        The minimum number of pages to show either side of the current page
        (defaults to ``3``)
    caps
        The number of pages to show at either end (defaults to ``1``)
    """
    def make_url(number):
        if number == 1 and first_page_url:
            return first_page_url
        match = RE_URL.match(url)
        if not match:
            raise template.TemplateSyntaxError(
                'URL did not contain the character "1" (which gets replaced with '
                'the actual page number).'
            )
        start, end = match.groups()
        return '%s%s%s' % (start, number, end)
    return get_page_context(page, make_url, adjacent, caps)


@register.inclusion_tag('pagination-nav.html')
def pagination_nav_qs(page, url='', querydict=None, url_attr='page',
                      adjacent=ADJACENT, caps=CAPS):
    """
    Generate Digg-like pagination navigation for URLs like "/entries/?page=5".

    Required arguments:

    page
        A django.core.paginator Page object

    Optional arguments:

    url
        The base url (defaults to a blank string)
    querydict
        Usually ``request.GET`` (defaults to an empty ``QueryDict``)
    url_attr
        The querystring attribute to change (defaults to ``'page'``)
    adjacent
        The minimum number of pages to show either side of the current page
        (defaults to ``3``)
    caps
        The number of pages to show at either end (defaults to ``1``)
    """
    querydict = querydict or QueryDict('')
    def make_url(number):
        qs = querydict.copy()
        if number == 1:
            qs.pop(url_attr, None)
        else:
            qs[url_attr] = number
        qs = qs.urlencode()
        if qs:
            qs = '?%s' % qs
        if not url and not qs:
            return '.'
        return '%s%s' % (url or '', qs)
    return get_page_context(page, make_url, adjacent, caps)
