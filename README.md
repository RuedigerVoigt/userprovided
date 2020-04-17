# userprovided

The package "userprovided" checks input for plausibility. For example it can check whether a string is a valid email address or an URL.

There are plenty of validators out there. The reasons to write another one:
* It's sister-project [exoskeleton](https://github.com/RuedigerVoigt/exoskeleton "GitHub Repository of exoskeleton") needs some special features. This would be for example not only to check whether a string is an URL, but to also check whether the scheme is http or https.
* Extensive testing (unittests and automatic test generation with the hypothesis package)
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

```
