# userprovided

The package "userprovided" checks input for plausibility. For example it can check whether a string is a valid email address or an URL.

There are plenty of validators out there. The reasons to write another one:
* Its sister-project [exoskeleton](https://github.com/RuedigerVoigt/exoskeleton "GitHub Repository of exoskeleton") needs some special features.
* Extensive testing (100% test coverage / unit tests / automatic test generation with the hypothesis package)
* Modularity

## Installation and Use

*Please take note that the development status of "userprovided" is "beta".* This means it may still contain some bugs and some commands could change with one of the next releases.

Install exoskeleton using `pip` or `pip3`. For example:

```pip install userprovided```

You may consider using a [virtualenv](https://virtualenv.pypa.io/en/latest/userguide/ "Documentation").


### Examples

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import userprovided

### Mailadresses ###

userprovided.mail.is_email(None)
# => False

userprovided.mail.is_email('example@example.com')
# => True

### Cloud ###

userprovided.cloud.is_aws_s3_bucket_name('foobar')
# => True


### URLs ###

print(userprovided.url.is_url('https://www.example.com'))
# => True

print(userprovided.url.is_url('https://www.example.com', ('ftp')))
# => False (Schema does not match permitted)


### Hashes ###

print(userprovided.hash.hash_available('md5'))
# => ValueError because md5 is deprecated

print(userprovided.hash.hash_available('sha256'))
# => True on almost any system

```

## Update and Deprecation Policy

It makes no sense to duplicate functionality already available in the Python Standard Library.

For example: `userprovided` does not contain methods to check IP addresses as the library [`ipaddress`](https://docs.python.org/3/library/ipaddress.html "documentation for the ipaddress library") is (since Python 3.3.) part of the standard.

If this package contains functionality that becomes superseded by the Standard Library, it will start to log a depreciation warning. The functionality itself is planned to stay available for at least a major version of `userprovided`.