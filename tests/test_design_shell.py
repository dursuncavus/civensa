"""The shell must preserve the pre-rollout navigation and period targets for every role."""
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

import pytest
from jinja2 import Environment, FileSystemLoader
from starlette.requests import Request


class Navigation(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = {}
        self.current = []
        self.inside = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'nav':
            self.inside = True
        if tag == 'a' and self.inside:
            self.links[attrs['href']] = attrs
            if attrs.get('aria-current') == 'page':
                self.current.append(attrs['href'])

    def handle_endtag(self, tag):
        if tag == 'nav':
            self.inside = False


@pytest.mark.parametrize('role,position', [('strategy', 'staff'), ('strategy', 'director'),
                                         ('department', 'staff'), ('department', 'director')])
@pytest.mark.parametrize('with_period', [False, True])
def test_shell_preserves_navigation_for_every_role(role, position, with_period):
    request = Request({'type': 'http', 'path': '/modules', 'scheme': 'http',
                       'server': ('testserver', 80), 'headers': [], 'session': {'csrf_token': 'synthetic'}})
    env = Environment(loader=FileSystemLoader(Path(__file__).resolve().parents[1] / 'app/templates'),
                      autoescape=True)
    context = dict(request=request, user=SimpleNamespace(role=role, position=position,
                   department_id=37, full_name='Örnek Kullanıcı'))
    if with_period:
        context['period'] = SimpleNamespace(id=81, year=2027)
    html = env.get_template('modules.html').render(**context)
    nav = Navigation()
    nav.feed(html)
    query = '?period_id=81' if with_period else ''
    expected = {'/activity-sections', '/modules', '/dashboard' + query}
    if with_period:
        expected.add('/source-comparison' + query)
    if role == 'strategy':
        expected |= {'/report-builder' + query, '/internal-control', '/budget-reallocations',
                     '/review' + query, '/activity-mapping' + query, '/operations' + query,
                     '/audit' + query, '/structure' + query, '/users' + query}
    else:
        expected |= {'/internal-control/our-actions', '/department/37' + query}
        if position == 'director':
            expected.add('/submit-authorizations' + query)
    assert set(nav.links) == expected
    assert nav.current == ['/modules']
    assert '<meta name="csrf-token" content="synthetic">' in html
    assert '<input type="hidden" name="csrf_token" value="synthetic">' in html
    assert '<form method="post" action="/logout">' in html
