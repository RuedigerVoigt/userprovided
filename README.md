# userprovided

![Supported Python Versions](https://img.shields.io/pypi/pyversions/userprovided)
![pypi version](https://img.shields.io/pypi/v/userprovided)
![Last commit](https://img.shields.io/github/last-commit/RuedigerVoigt/userprovided)
[![Downloads](https://pepy.tech/badge/userprovided)](https://pepy.tech/project/userprovided)
[![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)](https://www.ruediger-voigt.eu/coverage/userprovided/index.html)

*"Never trust user input!"* is also true outside the security context: You cannot be sure users always provide you with valid and well formatted data.

*The Python package `userprovided` checks input for validity and / or plausibility. Besides that it contains some methods to convert input into standardized formats.*

The code has type hints ([PEP 484](https://www.python.org/dev/peps/pep-0484/)) and aims to provide useful log and error messages.

Userprovided has functionality for the following inputs:
* [parameters](handle-parameters): [Check a dictionary](check-a-parameter-dictionary) for valid, needed, and unknown keys / convert lists, strings and tuples into a set / check if an integer or string is in a specific range / ...
* [url](handle-urls): [Normalize an URL](normalize-urls) and drop specific keys from the query part of it / Check if a string is an URL / [Determine a file extension]() from an URL and the Mime-type sent by the server.
* [hash](file-hashes): is the hash method available? / calculate a file hash and optionally compare it to an expected value.
* [date](handle-calendar-dates): Does a given date exist? / Convert English and German long format dates to ISO strings
* [mail](check-email-addresses): Check if a string is a valid email address






## Installation

Install exoskeleton using `pip` or `pip3`. For example:

```bash
sudo pip3 install userprovided
```

You may consider using a [virtualenv](https://virtualenv.pypa.io/en/latest/ "Documentation").

To upgrade to the latest version accordingly:

```bash
sudo pip install userprovided --upgrade
```

## Handle Parameters

### Check a Parameter Dictionary

If your application accepts parameters in the form of a dictionary, you have to test if all needed parameters are provided and if there are any unknown keys (maybe due to typos). There is a method for that:

```python
userprovided.parameters.validate_dict_keys(
    dict_to_check = {'a': 1, 'b': 2, 'c': 3},
    allowed_keys = {'a', 'b', 'c', 'd'},
    necessary_keys = {'b', 'c'})
```
Returns `True` if the dictionary `dict_to_check` contains only allowed keys and all necessary keys are present.

### Convert into a set

Convert a string, a tuple, or a list into a set (i.e. no duplicates, unordered):

```python
userprovided.parameters.convert_to_set(list)
```

### Check Range of Numbers and Strings


```python
def numeric_in_range(parameter_name,
                     given_value,
                     minimum_value,
                     maximum_value,
                     fallback_value) -> Union[int, float]



def string_in_range(string_to_check,
                    minimum_length,
                    maximum_lenght,
                    strip_string: bool = True) -> bool

userprovided.parameters.is_port(int)
# Checks if the port is integer and within the
# valid range from 0 to 65535.
```


## Handle URLs

### Normalize URLs

Normalize an URL means:
  * remove whitespace around it,
  * convert scheme and hostname to lowercase,
  * remove ports if they are the standard port for the scheme,
  * remove duplicate slashes from the path,
  * remove fragments (like #foo),
  * remove empty elements of the query part,
  * order the elements in the query part by alphabet

The optional parameter `drop_keys` allows you to remove specific keys, like session ids or trackers, from the query part of the URL.

```python
url = ' https://www.Example.com:443//index.py?c=3&a=1&b=2&d='
userprovided.url.normalize_url(url)
# returns: https://www.example.com/index.py?a=1&b=2&c=3
userprovided.url.normalize_url(url, drop_keys=['c'])
# returns: https://www.example.com/index.py?a=1&b=2
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


## Check Email Addresses

```python
userprovided.mail.is_email(None)
# => False

userprovided.mail.is_email('example@example.com')
# => True
```


## File Hashes

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

If you provide an expected value for the hash you can check for file changes or tampering. In the case the provided value and the calculated hash do *not* match, a ValueError exception is raised.

```python
userprovided.hash.calculate_file_hash(
    file_path = pathlib.Path('./foo.txt'),
    hash_method = 'sha512',
    expected_hash = 'not_the_right_value')
# => raises an exception
```

## Handle Calendar Dates

Does a specific date exist?

```python
userprovided.date.date_exists(2020, 2, 31)
# => False
```

Normalize German or English long form dates :

```python
userprovided.date.date_en_long_to_iso('October 3, 1990')
# => '1990-10-03'

userprovided.date.date_de_long_to_iso('3. Oktober 1990')
# => '1990-10-03'
```


## Update and Deprecation Policy

* No breaking changes in micro-versions.
* It makes no sense to duplicate functionality already available in the Python Standard Library. Therefore, if this package contains functionality that becomes superseded by the Standard Library, it will start to log a depreciation warning. The functionality itself is planned to stay available for at least a major version of `userprovided` and as long as Python versions not containing this functionality are supported.
