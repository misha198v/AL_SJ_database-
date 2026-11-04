from django.core.paginator import Paginator

def paginate(request, rows, per_page=10):
    page = Paginator(rows, per_page).get_page(request.GET.get('page', 1))
    def url(number):
        query = request.GET.copy()
        query['page'] = number
        return '?' + query.urlencode()
    return {
        'page': page, 'count': page.paginator.count,
        'previous_url': url(page.previous_page_number()) if page.has_previous() else None,
        'next_url': url(page.next_page_number()) if page.has_next() else None,
        'query': request.GET.get('q','').strip(),
        'has_filters': any(request.GET.get(k) for k in ('q','status','type')),
    }

def matches(row, query):
    return not query or query.casefold() in ' '.join(str(v or '') for v in row.values()).casefold()
