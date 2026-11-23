"""Unit tests for the syntax helpers in ``fathom.special``.

``test_special_types.py`` exercises special types through a whole profile.
These tests pin the four local syntax rules and the inference order one
level down, so a change to a rule shows up here with the exact input that
moved, not only as a changed count in a report.

Each rule has a violating input and a clean decoy (CHARTER: every check has
both). The rules are syntax and range checks only: nothing here looks up DNS,
deliverability, number allocation or ownership, and nothing classifies a
value as sensitive (spec 004).

Behaviour pinned as it stands on main; no expectation here changes it.
"""

import pytest

from fathom.special import email_domain, host_valid, infer_special, phone_digits, url_domain

NAME_REASON = 'Column name suggests'
VALUE_REASON = 'At least 80%'


# host_valid: an IP literal, or dotted labels of 1..63 letters/digits/hyphens.

@pytest.mark.parametrize('host', ['example.org', 'a-b.example.org', '1.2.3.4', '::1', 'a' * 63 + '.org'])
def test_host_valid_accepts(host):
    assert host_valid(host)


@pytest.mark.parametrize('host', [
    '',                 # empty
    'localhost',        # no dot: single-label hosts are not accepted
    'example.org.',     # trailing dot leaves an empty label
    '-bad.org',         # label starts with a hyphen
    'bad-.org',         # label ends with a hyphen
    'a' * 64 + '.org',  # label longer than 63
    'ex_ample.org',     # underscore is not a hostname character
])
def test_host_valid_rejects(host):
    assert not host_valid(host)


# email_domain: practical unquoted local part, valid host, domain casefolded.

@pytest.mark.parametrize('value,domain', [
    ('alpha@example.org', 'example.org'),
    ('Alpha@Example.ORG', 'example.org'),       # domain is casefolded for counting
    ("o'brien+tag@example.org", 'example.org'),  # permitted local punctuation
    ('a@1.2.3.4', '1.2.3.4'),                    # bare IP host passes host_valid
    ('x' * 64 + '@example.org', 'example.org'),  # local part at the 64 limit
])
def test_email_domain_accepts(value, domain):
    assert email_domain(value) == domain


@pytest.mark.parametrize('value', [
    'no-at-sign.example.org',
    'a@@example.org',        # more than one @
    '@example.org',          # empty local part
    '.a@example.org',        # leading dot
    'a.@example.org',        # trailing dot
    'a..b@example.org',      # consecutive dots
    'a b@example.org',       # space
    'a@localhost',           # single-label host
    'x' * 65 + '@example.org',  # local part over 64
])
def test_email_domain_rejects(value):
    assert email_domain(value) is None


# url_domain: http(s) only, a valid host, a port in 1..65535, no whitespace.

@pytest.mark.parametrize('value,domain', [
    ('https://example.org/path', 'example.org'),
    ('HTTP://Example.org', 'example.org'),       # scheme and host compared casefolded
    ('https://example.org:443/a', 'example.org'),
    ('http://[::1]/a', '::1'),                   # bracketed IPv6 literal
])
def test_url_domain_accepts(value, domain):
    assert url_domain(value) == domain


@pytest.mark.parametrize('value', [
    'ftp://example.org',          # scheme outside http(s)
    'example.org/path',           # no scheme
    'https:///broken',            # no host
    'http://bad host',            # whitespace
    'http://example.org:0/',      # port below range
    'http://example.org:99999/',  # port above range (urlsplit raises; caught)
    'http://localhost/',          # single-label host
])
def test_url_domain_rejects(value):
    assert url_domain(value) is None


# phone_digits: optional +, digits and ( ) . - space; 7..15 digits.

@pytest.mark.parametrize('value,digits', [
    ('+1 (202) 555-0101', '12025550101'),
    ('202.555.0101', '2025550101'),
    ('1234567', '1234567'),        # lower bound
    ('1' * 15, '1' * 15),          # upper bound
])
def test_phone_digits_accepts(value, digits):
    assert phone_digits(value) == digits


@pytest.mark.parametrize('value', ['123456', '1' * 16, '555-CALL', '202 555 0101 x12', '++1 202 555 0101'])
def test_phone_digits_rejects(value):
    assert phone_digits(value) is None


def test_phone_digits_alone_accepts_a_date_shape():
    # The helper is syntax only; infer_special is what keeps dates out (next test).
    assert phone_digits('2026-11-15') == '20261115'


# infer_special: names first (in a fixed order), then values (>=3 values, >=80%).

@pytest.mark.parametrize('name,typ', [
    ('lat', 'latitude'), ('Latitude', 'latitude'), ('start_lat', 'latitude'),
    ('lon', 'longitude'), ('LNG', 'longitude'), ('end-longitude', 'longitude'),
    ('email', 'email'), ('E-Mail', 'email'), ('contactEmail', 'email'),
    ('url', 'url'), ('Website', 'url'),
    ('phone', 'phone'), ('Home-Phone', 'phone'), ('mobile', 'phone'),
])
def test_name_rule_recognises_explicit_names(name, typ):
    typ_out, reason = infer_special([], name)
    assert typ_out == typ and reason.startswith(NAME_REASON)


@pytest.mark.parametrize('name', ['plate', 'along', 'salon', 'latte_count', 'id', ''])
def test_coordinate_names_need_a_token_boundary(name):
    # lat/lon/lng are matched as whole underscore-separated tokens only.
    assert infer_special(['x', 'y', 'z'], name) is None


def test_name_order_puts_coordinates_before_contact_types():
    assert infer_special([], 'lat_email')[0] == 'latitude'
    assert infer_special([], 'email_url')[0] == 'email'
    assert infer_special([], 'url_phone')[0] == 'url'


def test_value_rule_needs_three_values():
    assert infer_special(['a@example.org', 'b@example.org'], 'contact') is None
    assert infer_special(['a@example.org'] * 3, 'contact')[0] == 'email'


def test_value_rule_threshold_is_eighty_percent():
    good = 'a@example.org'
    assert infer_special([good] * 4 + ['nope'], 'contact')[0] == 'email'  # 4/5 = 80%
    assert infer_special([good] * 3 + ['nope'] * 2, 'contact') is None    # 3/5 = 60%


@pytest.mark.parametrize('values,typ', [
    (['https://example.org/a', 'http://example.org/b', 'https://example.com'], 'url'),
    (['+1 202 555 0101', '(202) 555-0102', '202-555-0103'], 'phone'),
])
def test_value_rule_recognises_formats(values, typ):
    typ_out, reason = infer_special(values, 'contact')
    assert typ_out == typ and reason.startswith(VALUE_REASON)


@pytest.mark.parametrize('values', [
    ['2025550101', '2025550102', '2025550103'],  # plain digits: could be any measurement or code
    ['2026-11-15', '2026-11-16', '2026-11-17'],  # dates have hyphens but parse as dates
])
def test_value_rule_does_not_call_numbers_or_dates_phones(values):
    assert infer_special(values, 'contact') is None
