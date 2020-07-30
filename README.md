# userprovided

![Supported Python Versions](https://img.shields.io/pypi/pyversions/userprovided)
![pypi version](https://img.shields.io/pypi/v/userprovided)
![Last commit](https://img.shields.io/github/last-commit/RuedigerVoigt/userprovided)
[![Downloads](https://pepy.tech/badge/userprovided)](https://pepy.tech/project/userprovided)

The package "userprovided" checks input for validity and / or plausibility. For example it can check whether a string is a valid email address or an URL. It can do more complicated tasks like checking a dictionary for valid and needed keys. It also contains some functionalities to convert input into a more rigid format (like the string 'October 3, 1990' into '1990-10-03').

There are plenty of validators out there. The reasons to write another one:
* Its sister-project [exoskeleton](https://github.com/RuedigerVoigt/exoskeleton "GitHub Repository of exoskeleton") needs some special features.
* Extensive testing (100% test coverage / unit tests / automatic test generation with the hypothesis package)
* The code has type hints ([PEP 484](https://www.python.org/dev/peps/pep-0484/))
* Modularity


## Update and Deprecation Policy

The development status of "userprovided" is "beta":
* Despite rigorous testing it might still contain some bugs.
* Some commands *could* change with one of the next releases. If possible function parameters will be kept unchanged. Sometimes optional parameters can be added to existing functions.

It makes no sense to duplicate functionality already available in the Python Standard Library. There is for example no function to check IP addresses as the library [`ipaddress`](https://docs.python.org/3/library/ipaddress.html "documentation for the ipaddress library") is part of the standard (since Python 3.3.).

If this package contains functionality that becomes superseded by the Standard Library, it will start to log a depreciation warning. The functionality itself is planned to stay available for at least a major version of `userprovided`.


## Installation and Use

Install exoskeleton using `pip` or `pip3`. For example:

```sudo pip install userprovided```

You may consider using a [virtualenv](https://virtualenv.pypa.io/en/latest/userguide/ "Documentation").

To upgrade to the latest version accordingly:
```sudo pip install userprovided --upgrade```

### Examples / Available Functions

```python
#!/usr/bin/env python3

import userprovided

### Cloud ###

userprovided.cloud.is_aws_s3_bucket_name('foobar')
# => True


### Dates ###

userprovided.date.date_exists(2020, 2, 31)
# => false

userprovided.date.date_en_long_to_iso('October 3, 1990')
# => '1990-10-03'


### Hashes ###

print(userprovided.hash.hash_available('md5'))
# => ValueError because md5 is deprecated

print(userprovided.hash.hash_available('sha256'))
# => True on almost any system

userprovided.hash.calculate_file_hash(pathlib.Path('./foo.txt'))
# Defaults to SHA256 and returns the hash of the file as a string.
# Also supports SHA224 and SHA512.


### Mailadresses ###

userprovided.mail.is_email(None)
# => False

userprovided.mail.is_email('example@example.com')
# => True


### Parameters ###

userprovided.parameters.convert_to_set(list)
# => Convert a string, a tuple, or a list into a set
# (i.e. no duplicates, unordered)


userprovided.parameters.validate_dict_keys(
    dict_to_check = {'a': 1, 'b': 2, 'c': 3},
    allowed_keys = {'a', 'b', 'c', 'd'},
    necessary_keys = {'b', 'c'})
# => True
# The dictionary contains only allowed keys and
# all necessary keys are present.

### Ports ###

userprovided.port.port_in_range(int)
# Checks if the port is integer and within the
# valid range from 0 to 65536.

### URLs ###

print(userprovided.url.is_url('https://www.example.com'))
# => True

print(userprovided.url.is_url('https://www.example.com', ('ftp')))
# => False (Schema does not match permitted)
```
