# userprovided

![Supported Python Versions](https://img.shields.io/pypi/pyversions/userprovided)
![pypi version](https://img.shields.io/pypi/v/userprovided)
![Last commit](https://img.shields.io/github/last-commit/RuedigerVoigt/userprovided)
[![Downloads](https://pepy.tech/badge/userprovided)](https://pepy.tech/project/userprovided)
[![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen)](https://www.ruediger-voigt.eu/coverage/userprovided/index.html)

The Python package `userprovided` checks input for validity and / or plausibility. For example it can check whether a string is a valid email address or an URL. It can do more complicated tasks like checking a dictionary for valid and needed keys. It also contains some functionalities to convert input into a more rigid format (like the string 'October 3, 1990' into '1990-10-03').

There are similar projects out there. The reasons to write another library:
* Extensive testing.
* The code has type hints ([PEP 484](https://www.python.org/dev/peps/pep-0484/)).
* Its sister-projects like [exoskeleton](https://github.com/RuedigerVoigt/exoskeleton "a crawler framework") and [salted](https://github.com/RuedigerVoigt/salted "a smart and very fast linkchecker") need some special features. This reduces the dependency on a third party to apply patches or to keep up with development.
* Modularity


## Update and Deprecation Policy

* No breaking changes in micro-versions.
* It makes no sense to duplicate functionality already available in the Python Standard Library. Therefore, if this package contains functionality that becomes superseded by the Standard Library, it will start to log a depreciation warning. The functionality itself is planned to stay available for at least a major version of `userprovided` and as long as Python versions not containing this functionality are supported.

## Documentation

### Installation

Install exoskeleton using `pip` or `pip3`. For example:

```bash
sudo pip3 install userprovided
```

You may consider using a [virtualenv](https://virtualenv.pypa.io/en/latest/userguide/ "Documentation").

To upgrade to the latest version accordingly:

```bash
sudo pip install userprovided --upgrade
```

### Check a Parameter Dictionary

If your application accepts parameters in the form of a dictionary, you have to test if all needed parameters are provided and if there are any unknown keys (maybe due to typos). There is a method for that:

```python
userprovided.parameters.validate_dict_keys(
    dict_to_check = {'a': 1, 'b': 2, 'c': 3},
    allowed_keys = {'a', 'b', 'c', 'd'},
    necessary_keys = {'b', 'c'})
```
Returns `True` if the dictionary `dict_to_check` contains only allowed keys and all necessary keys are present.

### Normalize URLs

Normalize an URL means:
  * remove whitespace around it,
  * convert scheme and hostname to lowercase,
  * remove ports if they are the standard port for the scheme,
  * remove duplicate slashes from the path,
  * remove fragments (like #foo),
  * remove empty elements of the query part,
  * order the elements in the query part by alphabet

```python
url = ' https://www.Example.com:443//index.py?c=3&a=1&b=2&d='
userprovided.url.normalize_url(url)
# returns: https://www.example.com/index.py?a=1&b=2&c=3
```

### Check Email-Addresses

```python
userprovided.mail.is_email(None)
# => False

userprovided.mail.is_email('example@example.com')
# => True
```

### Check URLs

To check whether a string is a valid URL - including a scheme (like `https`) - use `userprovided.url.is_url`. 

```python
userprovided.url.is_url('https://www.example.com')
# => True
userprovided.url.is_url('www.example.com')
# => False
```

You can insist on a specific scheme:

```python
userprovided.url.is_url('https://www.example.com', ('ftp'))
# => False (Schema does not match permitted)

userprovided.url.is_url('ftp://www.example.com', ('ftp'))
# => True
```

### File Hashes

You can check whether a specific hash method is available. This will raise a ValueError for `MD5` and `SHA1` *even if they are available*, because they are deprecated.

```python
print(userprovided.hash.hash_available('md5'))
# => ValueError because md5 is deprecated

print(userprovided.hash.hash_available('sha256'))
# => True on almost any system
```

You can calculate hash sums for files. If you do not provide the method, this defaults to `SHA256`. Other supported methods are `SHA224` and `SHA512`.

```python
# returns the hash of the file as a string:
userprovided.hash.calculate_file_hash(pathlib.Path('./foo.txt'))
```

### Check and Normalize Dates

```python
userprovided.date.date_exists(2020, 2, 31)
# => False

userprovided.date.date_en_long_to_iso('October 3, 1990')
# => '1990-10-03'
```


### Other Functionality

```python
### Cloud ###

userprovided.cloud.is_aws_s3_bucket_name('foobar')
# => True

### Parameters ###

userprovided.parameters.convert_to_set(list)
# => Convert a string, a tuple, or a list into a set
# (i.e. no duplicates, unordered)

### Ports ###

userprovided.port.port_in_range(int)
# Checks if the port is integer and within the
# valid range from 0 to 65536.
```
