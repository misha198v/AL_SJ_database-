from datetime import datetime, timedelta
from decimal import Decimal
from django import template
from django.utils import timezone
from django.utils.html import format_html
register = template.Library()
ICONS = {"plane":"m22 2-7 20-4-9-9-4 20-7Z M22 2 11 13","grid":"M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z","files":"M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z M14 2v6h6 M8 13h8 M8 17h5","route":"M5 5a2 2 0 1 0 .01 0 M19 19a2 2 0 1 0 .01 0 M7 5h8a4 4 0 0 1 0 8H9a3 3 0 0 0 0 6h8","clock":"M12 3a9 9 0 1 0 .01 0 M12 7v5l3 2","calendar":"M8 2v4 M16 2v4 M3 10h18 M5 4h14a2 2 0 0 1 2 2v14H3V6a2 2 0 0 1 2-2 M7 14h3 M14 14h3 M7 18h3","users":"M9 11a4 4 0 1 0 .01 0 M2 21v-2a6 6 0 0 1 12 0v2 M17 3a4 4 0 0 1 0 8 M17 15a5 5 0 0 1 5 5v1","chart":"M4 3v18h17 M8 16v-5 M13 16V6 M18 16v-8","search":"M10.5 3a7.5 7.5 0 1 0 .01 0 M16 16l5 5","arrow":"M4 12h16 M14 6l6 6-6 6","chevron":"m9 5 7 7-7 7","check":"m5 12 4 4L19 6","close":"m6 6 12 12 M6 18 18 6","logout":"M9 4H4v16h5 M13 8l4 4-4 4 M9 12h12","shield":"m12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6l9-4 M8 12l3 3 5-6","mail":"M3 5h18v14H3z M3 5l9 7 9-7","wallet":"M3 5h16v4 M3 5v14h18V9H3 M16 14h2","database":"M21 5c0 2-4 3-9 3S3 7 3 5s4-3 9-3 9 1 9 3Z M3 5v14c0 4 18 4 18 0V5 M3 12c0 4 18 4 18 0","menu":"M4 6h16 M4 12h16 M4 18h16","eye":"M2 12s3-7 10-7 10 7 10 7-3 7-10 7S2 12 2 12 M12 9a3 3 0 1 0 .01 0","download":"M12 3v12 M7 10l5 5 5-5 M4 16v5h16v-5","pin":"M12 22s8-8 8-13a8 8 0 1 0-16 0c0 5 8 13 8 13 M12 6a3 3 0 1 0 .01 0","plus":"M12 4v16 M4 12h16","info":"M12 3a9 9 0 1 0 .01 0 M12 11v6 M12 7v.1","trash":"M3 6h18 M9 6V3h6v3 M5 6l1 15h12l1-15 M10 10v7 M14 10v7","spark":"m12 3 2.3 6.7L21 12l-6.7 2.3L12 21l-2.3-6.7L3 12l6.7-2.3L12 3Z"}
@register.simple_tag
def icon(name, css=''):
    path = ICONS.get(name, ICONS['files'])
    return format_html('<svg class="icon {}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="{}"/></svg>', css, path)

@register.filter
def humanize(value):
    return str(value or '').replace('_',' ').replace('ID','ID').title()

@register.filter
def initial(value):
    return ''.join(part[0] for part in str(value or '').split()[:2]).upper()

@register.filter
def short_id(value):
    return str(value or '')[-8:].upper()

@register.filter
def duration(value):
    if value is None:
        return 'In progress'
    seconds = int(value.total_seconds())
    return f'{seconds // 3600}h {(seconds % 3600) // 60:02d}m'

@register.filter
def display(value):
    if value is None:
        return '—'
    if isinstance(value, bool):
        return 'Yes' if value else 'No'
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime('%d %b %Y, %H:%M')
    if isinstance(value, timedelta):
        return duration(value)
    if isinstance(value, Decimal):
        return f'{value:,.2f}'
    return str(value)

@register.filter
def status_style(value):
    word = str(value).upper()
    if word in ('VERIFIED','COMPLETED','SENT','DELIVERED','ACTIVE'):
        return 'success'
    if word in ('PENDING','UPCOMING','IN_PROGRESS','REGISTERED'):
        return 'warning'
    if word in ('REJECTED','FAILED','CANCELLED'):
        return 'danger'
    if word in ('REFUNDED','CLOSED','ARCHIVED'):
        return 'neutral'
    return ''

@register.filter
def get_item(value, key):
    return value.get(key, '') if hasattr(value,'get') else ''

@register.simple_tag(takes_context=True)
def query_url(context, **changes):
    query = context['request'].GET.copy()
    for key,value in changes.items():
        if value is None or value == '':
            query.pop(key,None)
        else:
            query[key] = value
    return '?' + query.urlencode()
