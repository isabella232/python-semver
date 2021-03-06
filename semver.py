"""
Python helper for Semantic Versioning (http://semver.org/)

Examples:
>>> import semver
>>> semver.compare("1.0.0", "2.0.0")
-1
>>> semver.compare("2.0.0", "1.0.0")
1
>>> semver.compare("2.0.0", "2.0.0")
0
>>> semver.match("2.0.0", ">=1.0.0")
True
>>> semver.match("1.0.0", ">1.0.0")
False
>>> semver.format_version(3, 4, 5, 'pre.2', 'build.4')
'3.4.5-pre.2+build.4'
>>> version_parts = semver.parse("3.4.5-pre.2+build.4")
>>> version_parts == {
...     'major': 3, 'minor': 4, 'patch': 5,
...     'prerelease': 'pre.2', 'build': 'build.4'}
True
>>> version_info = semver.parse_version_info("3.4.5-pre.2+build.4")
>>> version_info
VersionInfo(major=3, minor=4, patch=5, prerelease='pre.2', build='build.4')
>>> version_info.major
3
>>> version_info > (1, 0)
True
>>> version_info < (3, 5)
True
>>> semver.bump_major("3.4.5")
'4.0.0'
>>> semver.bump_minor("3.4.5")
'3.5.0'
>>> semver.bump_patch("3.4.5")
'3.4.6'
>>> semver.max_ver("1.0.0", "2.0.0")
'2.0.0'
>>> semver.min_ver("1.0.0", "2.0.0")
'1.0.0'
"""

import collections
import re
import sys


__version__ = '2.7.3'
__author__ = 'Kostiantyn Rybnikov'
__author_email__ = 'k-bx@k-bx.com'

# Lenient mode is off by default
lenient = False

_LAST_NUMBER = re.compile(r'(?:[^\d]*(\d+)[^\d]*)+')

if not hasattr(__builtins__, 'cmp'):
    def cmp(a, b):
        if lenient:
            if a is not None and b is not None:
                return (a > b) - (a < b)
            elif a is not None and b is None:
                return 1
            elif a is None and b is not None:
                return -1
            else:
                return 0
        else:
            return (a > b) - (a < b)


def set_lenient(a):
    global lenient
    lenient = a


def get_regex():
    if lenient:
        return re.compile(
            r"""
            ^
            (?P<major>(?:0|[1-9][0-9]*))
            (
                \.
                (?P<minor>(?:0|[1-9][0-9]*))
                (
                    \.
                    (?P<patch>(?:0|[1-9][0-9]*))
                    (\-(?P<prerelease>
                        (?:0|[1-9A-Za-z-][0-9A-Za-z-]*)
                        (\.(?:0|[1-9A-Za-z-][0-9A-Za-z-]*))*
                    ))?
                    ((\+|\.)(?P<build>
                        [0-9A-Za-z-]+
                        (\.[0-9A-Za-z-]+)*
                    ))?
                )?
            )?
            $
            """, re.VERBOSE)
    else:
        return re.compile(
            r"""
            ^
            (?P<major>(?:0|[1-9][0-9]*))
            \.
            (?P<minor>(?:0|[1-9][0-9]*))
            \.
            (?P<patch>(?:0|[1-9][0-9]*))
            (\-(?P<prerelease>
                (?:0|[1-9A-Za-z-][0-9A-Za-z-]*)
                (\.(?:0|[1-9A-Za-z-][0-9A-Za-z-]*))*
            ))?
            (\+(?P<build>
                [0-9A-Za-z-]+
                (\.[0-9A-Za-z-]+)*
            ))?
            $
            """, re.VERBOSE)


def parse(version):
    """Parse version to major, minor, patch, pre-release, build parts.

    :param version: version string
    :return: dictionary with the keys 'build', 'major', 'minor', 'patch',
             and 'prerelease'. The prerelease or build keys can be None
             if not provided
    :rtype: dict
    """
    match = get_regex().match(version)
    if match is None:
        raise ValueError('%s is not valid SemVer string' % version)

    version_parts = match.groupdict()

    version_parts['major'] = int(version_parts['major'])
    if lenient:
        if version_parts['minor'] is not None:
            version_parts['minor'] = int(version_parts['minor'])
        else:
            version_parts['minor'] = 0

        if version_parts['patch'] is not None:
            version_parts['patch'] = int(version_parts['patch'])
        else:
            version_parts['patch'] = 0
    else:
        version_parts['minor'] = int(version_parts['minor'])
        version_parts['patch'] = int(version_parts['patch'])

    return version_parts


VersionInfo = collections.namedtuple(
        'VersionInfo', 'major minor patch prerelease build')

# Only change it for Python > 3 as it is readonly
# for version 2
if sys.version_info > (3, 0):
    VersionInfo.__doc__ = """
:param int major: version when you make incompatible API changes.
:param int minor: version when you add functionality in
                  a backwards-compatible manner.
:param int patch: version when you make backwards-compatible bug fixes.
:param str prerelease: an optional prerelease string
:param str build: an optional build string

>>> import semver
>>> ver = semver.parse('3.4.5-pre.2+build.4')
>>> ver
{'build': 'build.4', 'major': 3, 'minor': 4, 'patch': 5,
'prerelease': 'pre.2'}
"""


def parse_version_info(version):
    """Parse version string to a VersionInfo instance.

    :param version: version string
    :return: a :class:`VersionInfo` instance
    :rtype: :class:`VersionInfo`
    """
    parts = parse(version)
    version_info = VersionInfo(
            parts['major'], parts['minor'], parts['patch'],
            parts['prerelease'], parts['build'])

    return version_info


def compare(ver1, ver2):
    """Compare two versions

    :param ver1: version string 1
    :param ver2: version string 2
    :return: The return value is negative if ver1 < ver2,
             zero if ver1 == ver2 and strictly positive if ver1 > ver2
    :rtype: int
    """
    def nat_cmp(a, b):
        def convert(text):
            return (2, int(text)) if re.match('[0-9]+', text) else (1, text)

        def split_key(key):
            return [convert(c) for c in key.split('.')]

        a, b = a or '', b or ''
        return cmp(split_key(a), split_key(b))

    def compare_by_keys(d1, d2):
        for key in ['major', 'minor', 'patch']:
            v = cmp(d1.get(key), d2.get(key))
            if v:
                return v

        rc1, rc2 = d1.get('prerelease'), d2.get('prerelease')
        rccmp = nat_cmp(rc1, rc2)

        if not rccmp:
            return 0
        if not rc1:
            return 1
        elif not rc2:
            return -1

        return rccmp

    v1, v2 = parse(ver1), parse(ver2)

    return compare_by_keys(v1, v2)


def match(version, match_expr):
    """Compare two versions through a comparison

    :param str version: a version string
    :param str match_expr: operator and version; valid operators are
          <   smaller than
          >   greater than
          >=  greator or equal than
          <=  smaller or equal than
          ==  equal
          !=  not equal
    :return: True if the expression matches the version, otherwise False
    :rtype: bool
    """
    prefix = match_expr[:2]
    if prefix in ('>=', '<=', '==', '!='):
        match_version = match_expr[2:]
    elif prefix and prefix[0] in ('>', '<'):
        prefix = prefix[0]
        match_version = match_expr[1:]
    else:
        raise ValueError("match_expr parameter should be in format <op><ver>, "
                         "where <op> is one of "
                         "['<', '>', '==', '<=', '>=', '!=']. "
                         "You provided: %r" % match_expr)

    possibilities_dict = {
        '>': (1,),
        '<': (-1,),
        '==': (0,),
        '!=': (-1, 1),
        '>=': (0, 1),
        '<=': (-1, 0)
    }

    possibilities = possibilities_dict[prefix]
    cmp_res = compare(version, match_version)

    return cmp_res in possibilities


def max_ver(ver1, ver2):
    """Returns the greater version of two versions

    :param ver1: version string 1
    :param ver2: version string 2
    :return: the greater version of the two
    :rtype: :class:`VersionInfo`
    """
    cmp_res = compare(ver1, ver2)
    if cmp_res == 0 or cmp_res == 1:
        return ver1
    else:
        return ver2


def min_ver(ver1, ver2):
    """Returns the smaller version of two versions

    :param ver1: version string 1
    :param ver2: version string 2
    :return: the smaller version of the two
    :rtype: :class:`VersionInfo`
    """
    cmp_res = compare(ver1, ver2)
    if cmp_res == 0 or cmp_res == -1:
        return ver1
    else:
        return ver2


def format_version(major, minor, patch, prerelease=None, build=None):
    """Format a version according to the Semantic Versioning specification

    :param str major: the required major part of a version
    :param str minor: the required minor part of a version
    :param str patch: the required patch part of a version
    :param str prerelease: the optional prerelease part of a version
    :param str build: the optional build part of a version
    :return: the formatted string
    :rtype: str
    """
    version = "%d.%d.%d" % (major, minor, patch)
    if prerelease is not None:
        version = version + "-%s" % prerelease

    if build is not None:
        version = version + "+%s" % build

    return version


def _increment_string(string):
    """
    Look for the last sequence of number(s) in a string and increment, from:
    http://code.activestate.com/recipes/442460-increment-numbers-in-a-string/#c1
    """
    match = _LAST_NUMBER.search(string)
    if match:
        next_ = str(int(match.group(1)) + 1)
        start, end = match.span(1)
        string = string[:max(end - len(next_), start)] + next_ + string[end:]
    return string


def bump_major(version):
    """Raise the major part of the version

    :param: version string
    :return: the raised version string
    :rtype: str
    """
    verinfo = parse(version)
    return format_version(verinfo['major'] + 1, 0, 0)


def bump_minor(version):
    """Raise the minor part of the version

    :param: version string
    :return: the raised version string
    :rtype: str
    """
    verinfo = parse(version)
    return format_version(verinfo['major'], verinfo['minor'] + 1, 0)


def bump_patch(version):
    """Raise the patch part of the version

    :param: version string
    :return: the raised version string
    :rtype: str
    """
    verinfo = parse(version)
    return format_version(verinfo['major'], verinfo['minor'],
                          verinfo['patch'] + 1)


def bump_prerelease(version):
    """Raise the prerelease part of the version

    :param: version string
    :return: the raised version string
    :rtype: str
    """
    verinfo = parse(version)
    verinfo['prerelease'] = _increment_string(verinfo['prerelease'] or 'rc.0')
    return format_version(verinfo['major'], verinfo['minor'], verinfo['patch'],
                          verinfo['prerelease'])


def bump_build(version):
    """Raise the build part of the version

    :param: version string
    :return: the raised version string
    :rtype: str
    """
    verinfo = parse(version)
    verinfo['build'] = _increment_string(verinfo['build'] or 'build.0')
    return format_version(verinfo['major'], verinfo['minor'], verinfo['patch'],
                          verinfo['prerelease'], verinfo['build'])
