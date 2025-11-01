# userprovided

![Supported Python Versions](https://img.shields.io/pypi/pyversions/userprovided)
![pypi version](https://img.shields.io/pypi/v/userprovided)
![Last commit](https://img.shields.io/github/last-commit/RuedigerVoigt/userprovided)
[![Downloads](https://pepy.tech/badge/userprovided)](https://pepy.tech/project/userprovided)
![Coverage](https://img.shields.io/badge/coverage-99%25-brightgreen)

*"Never trust user input!"* is also true outside the security context: You cannot be sure users always provide you with valid and well-formatted data.
For a wide range of data, the Python package `userprovided`:
* checks for validity and plausibility
* normalizes input
* converts into standardized formats
* performs basic security checks

The code has type hints ([PEP 484](https://www.python.org/dev/peps/pep-0484/)) and provides useful log and error messages.

Userprovided has functionality for the following inputs:
* [parameters](#handle-parameters):
  * [Check a dictionary](#check-a-parameter-dictionary) for valid, needed, and unknown keys.
  * [Avoid keys without value in a dictionary](#avoid-keys-without-value-in-a-dictionary) to ensure all values are present.
  * [Convert into a set](#convert-into-a-set) from lists, strings and tuples.
  * [Parse separated strings into a set](#parse-separated-strings-into-a-set) with support for quotes and escaping.
  * [Check range of numbers and strings](#check-range-of-numbers-and-strings) to validate if values are in a specific range.
  * [Check integer range](#check-integer-range) with strict integer type enforcement.
  * [Enforce boolean type](#enforce-boolean-type) to reject truthy/falsy values.
  * [Validate AWS S3 bucket names](#validate-aws-s3-bucket-names) against AWS naming rules.
* [url](#handle-urls):
  * [Normalize a URL](#normalize-urls) and drop specific keys from the query part of it.
  * [Check](#check-urls) if a string is a URL.
  * [Check for shortened URLs](#check-for-shortened-urls) from known URL shortening services.
  * [Determine a file extension](#determine-a-file-extension) from a URL and the MIME-type sent by the server.
  * [Extract domain from URL](#extract-domain-from-url) with optional subdomain removal, supporting 2-part TLDs.
  * [Extract TLD from URL](#extract-tld-from-url) correctly identifying both standard and 2-part TLDs.
* [hash](#hashes):
  * [Is the hash method available?](#check-hash-availability)
  * [Calculate a file hash](#calculate-a-file-hash) and (optionally) compare it to an expected value.
  * [Calculate a string hash](#calculate-string-hash) for non-security use cases like cache keys.
* [date](#handle-calendar-dates):
  * [Does a given date exist?](#check-date-existence)
  * Convert English and German [long format dates to ISO](#normalize-long-form-dates) strings.
* [mail](#check-email-addresses):
  * Check if a string is a valid email address.
* [geo](#validate-geographic-coordinates):
  * [Validate coordinates](#validate-geographic-coordinates) to check if latitude and longitude are within valid Earth ranges.






## Installation

Install userprovided using `pip` or `pip3`. For example:

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

### Avoid Keys without Value in a Dictionary

Check if all keys in a dictionary have a value. Return `False` if the value for any key is empty. Works for strings (including whitespace only), dictionaries, lists, tuples, and sets.

```python
# returns True:
parameters.keys_neither_none_nor_empty({'a': 123, 'b': 'example'})

# returns False:
parameters.keys_neither_none_nor_empty({'a': '   ', 'b': 'example'})
parameters.keys_neither_none_nor_empty({'a': None, 'b': 'example'})
parameters.keys_neither_none_nor_empty({'a': list(), 'b': 'example'})
```

### Convert into a set

Convert a string, a tuple, or a list into a set (i.e. no duplicates, unordered):

```python
userprovided.parameters.convert_to_set(list)
```

### Parse Separated Strings into a Set

Parse comma-separated (or custom separator) strings into a set of trimmed, non-empty values. This function supports:
- Custom separators (default: comma)
- Quoted fields to include the separator character within values
- Backslash escaping for special characters
- Automatic trimming and deduplication

```python
# Basic comma-separated values
userprovided.parameters.separated_string_to_set('a, b, c')
# => {'a', 'b', 'c'}

# Quoted fields with separator inside
userprovided.parameters.separated_string_to_set('"hello, world", foo, bar')
# => {'hello, world', 'foo', 'bar'}

# Escaped separator
userprovided.parameters.separated_string_to_set('a\\,b, c')
# => {'a,b', 'c'}

# Custom separator
userprovided.parameters.separated_string_to_set('a|b|c', sep='|')
# => {'a', 'b', 'c'}

# Empty fields and whitespace are handled
userprovided.parameters.separated_string_to_set('a, , b,  ,c')
# => {'a', 'b', 'c'}

# Disable quote parsing if needed
userprovided.parameters.separated_string_to_set('"a,b",c', allow_quotes=False)
# => {'"a', 'b"', 'c'}

# Returns None for None input
userprovided.parameters.separated_string_to_set(None)
# => None
```

**Parameters:**
- `raw_string`: The string to parse (or None)
- `sep`: Separator character (default: `','`)
- `allow_quotes`: Enable quote parsing (default: `True`)
- `quote_char`: Quote character (default: `'"'`)

**Raises:**
- `ValueError`: If separator/quote_char is not a single character, if quote_char equals separator, or if quotes are unclosed

### Check Range of Numbers and Strings


```python
def numeric_in_range(parameter_name,
                     given_value,
                     minimum_value,
                     maximum_value,
                     fallback_value) -> Union[int, float]



def string_in_range(string_to_check,
                    minimum_length,
                    maximum_length,
                    strip_string: bool = True) -> bool

userprovided.parameters.is_port(int)
# Checks if the port is integer and within the
# valid range from 0 to 65535.
```

### Check Integer Range

Similar to `numeric_in_range`, but with strict type checking to ensure all values are exactly integers (not floats). This is useful when you need to guarantee integer types, for example when working with array indices, counts, or IDs.

```python
# Returns the value if within range
userprovided.parameters.int_in_range(
    parameter_name='user_age',
    given_value=25,
    minimum_value=0,
    maximum_value=120,
    fallback_value=18
)
# => 25

# Returns fallback if out of range
userprovided.parameters.int_in_range(
    parameter_name='page_number',
    given_value=500,
    minimum_value=1,
    maximum_value=100,
    fallback_value=1
)
# => 1 (fallback value, logs warning)

# Rejects floats even if they represent whole numbers
userprovided.parameters.int_in_range(
    parameter_name='count',
    given_value=5.0,  # This is a float, not an int
    minimum_value=1,
    maximum_value=10,
    fallback_value=5
)
# => ValueError: Value must be an integer.
```

The function validates that minimum ≤ maximum and that the fallback value is within the allowed range.

### Enforce Boolean Type

Validates that a parameter is exactly of type `bool` (True or False), not just a truthy or falsy value. Use this when you need to ensure strict boolean parameters and avoid subtle bugs from implicit type conversions.

```python
# Valid boolean values pass
userprovided.parameters.enforce_boolean(True)
# => No error

userprovided.parameters.enforce_boolean(False, parameter_name='debug_mode')
# => No error

# Truthy/falsy values are rejected
userprovided.parameters.enforce_boolean(1)
# => ValueError: Value of parameter must be boolean, i.e True / False

userprovided.parameters.enforce_boolean('true')
# => ValueError: Value of parameter must be boolean, i.e True / False
```

### Validate AWS S3 Bucket Names

Check if a string complies with AWS S3 bucket naming rules. AWS has strict requirements for bucket names to ensure they work properly across all regions and services.

```python
userprovided.parameters.is_aws_s3_bucket_name('my-valid-bucket-name')
# => True

userprovided.parameters.is_aws_s3_bucket_name('192.168.1.1')
# => False (cannot resemble IP address)

userprovided.parameters.is_aws_s3_bucket_name('xn--bucket')
# => False (cannot start with 'xn--')

userprovided.parameters.is_aws_s3_bucket_name('bucket-s3alias')
# => False (cannot end with '-s3alias')
```

AWS S3 bucket name requirements enforced:
- Length: 3-63 characters
- Allowed characters: lowercase letters, numbers, hyphens, and dots
- Must start and end with a letter or number
- Cannot resemble an IP address (e.g., 192.168.1.1)
- Cannot contain consecutive dots (..) or dot-hyphen combinations (.- or -.)
- Cannot start with reserved prefixes: `xn--`, `sthree-`, `amzn-s3-demo-`
- Cannot end with reserved suffixes: `-s3alias`, `--ol-s3`, `.mrap`, `--x-s3`, `--table-s3`


## Handle URLs

### Normalize URLs

Normalizing a URL means:
  * remove whitespace around it,
  * convert scheme and hostname to lowercase,
  * remove ports if they are the standard port for the scheme,
  * remove duplicate slashes from the path,
  * remove fragments (like #foo),
  * remove empty elements of the query part,
  * order the elements in the query part alphabetically

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
# => False (Schema is not permitted)

userprovided.url.is_url('ftp://www.example.com', ('ftp'))
# => True
```

To check the URL with an actual connection attempt, you could use the [salted library](https://github.com/RuedigerVoigt/salted).


### Check for Shortened URLs

Check whether a URL is from a known URL shortening service. Such URLs can be useful and harmless, but could also be a way for an attacker to disguise the target of a link.

```python
userprovided.url.is_shortened_url('https://bit.ly/example')
# => True

userprovided.url.is_shortened_url('https://www.example.com/page')
# => False

userprovided.url.is_shortened_url('https://youtu.be/dQw4w9WgXcQ')
# => False (platform-specific shorteners like youtu.be are not included)
```

This function recognizes a list of 22 popular URL shortening services that allow random targets. By design, it will *not* recognize platform-specific short URLs like `youtu.be` as they point to a specific platform (YouTube) rather than arbitrary destinations.


### Determine a File Extension

Guess the correct filename extension from a URL and / or the mime-type returned by the server.
Sometimes a valid URL does not contain a file extension (like `https://www.example.com/`), or it is ambiguous.
So the mime type acts as a fallback. In case the correct extension cannot be determined at all, it is set to 'unknown'.

```python
# returns '.html'
userprovided.url.determine_file_extension(
    url='https://www.example.com',
    provided_mime_type='text/html'
)

# returns '.pdf'
userprovided.url.determine_file_extension(
    'https://www.example.com/example.pdf',
    None
)
```

### Extract Domain from URL

Extract the domain (hostname) from a URL, with optional subdomain removal. Correctly handles 2-part TLDs like `.co.uk` and `.com.au`, and returns IP addresses and localhost unchanged.

```python
# Extract full domain with subdomain
userprovided.url.extract_domain('https://www.example.com:8080/path')
# => 'www.example.com'

# Drop subdomain to get registrable domain
userprovided.url.extract_domain('https://www.example.com', drop_subdomain=True)
# => 'example.com'

# Correctly handles 2-part TLDs
userprovided.url.extract_domain('https://subdomain.example.co.uk/page', drop_subdomain=True)
# => 'example.co.uk'

userprovided.url.extract_domain('https://www.example.com.au/page', drop_subdomain=True)
# => 'example.com.au'

# IP addresses and localhost are returned as-is
userprovided.url.extract_domain('http://192.168.1.1:8080/path', drop_subdomain=True)
# => '192.168.1.1'

userprovided.url.extract_domain('http://localhost:3000', drop_subdomain=True)
# => 'localhost'
```

### Extract TLD from URL

Extract the top-level domain (TLD) from a URL. Correctly identifies 2-part TLDs like `.co.uk` and `.com.au`, returning them as a single unit.

```python
# Standard single-part TLD
userprovided.url.extract_tld('https://www.example.com/path')
# => '.com'

# 2-part TLD examples
userprovided.url.extract_tld('https://example.co.uk')
# => '.co.uk'

userprovided.url.extract_tld('https://subdomain.example.com.au/page')
# => '.com.au'

# IP addresses and localhost have no TLD
userprovided.url.extract_tld('http://192.168.1.1')
# => ''

userprovided.url.extract_tld('http://localhost')
# => ''
```

## Check Email Addresses

```python
userprovided.mail.is_email('example@example.com')
# => True

userprovided.mail.is_email('example+test@example.com')
# => True

userprovided.mail.is_email('invalid.email')
# => False
```


## Hashes

### Check Hash Availability

You can check whether a specific hash method is available. This will raise a DeprecatedHashAlgorithm exception for `MD5` and `SHA1` *even if they are available*, because they are deprecated.

```python
print(userprovided.hash.hash_available('md5'))
# => DeprecatedHashAlgorithm exception because md5 is deprecated

print(userprovided.hash.hash_available('sha256'))
# => True on almost any system
```

### Calculate a file hash

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

### Calculate String Hash

Compute a deterministic hash of string data for non-security use cases such as fingerprints, cache keys, or content de-duplication.

```python
userprovided.hash.calculate_string_hash('example data')
# => returns the SHA256 hash as a string

userprovided.hash.calculate_string_hash('example data', hash_method='sha512')
# => returns the SHA512 hash as a string

userprovided.hash.calculate_string_hash('example data', encoding='utf-8')
# => specify encoding (defaults to utf-8)
```

**Important Security Warning:** Do NOT use this function for:
- Password storage
- Message integrity/authenticity
- Anything needing resistance to brute force or active attackers

This is a generic hash utility for non-security scenarios only. For security-sensitive applications, use proper cryptographic libraries with salting, key derivation functions (like bcrypt, scrypt, or Argon2), or HMAC.

The function supports the same hash methods as `calculate_file_hash`: SHA224, SHA256 (default), SHA384, SHA512, SHA3 variants, BLAKE2 variants, and other algorithms available in hashlib, but rejects deprecated algorithms (MD5, SHA1).

## Handle Calendar Dates

### Check Date Existence

Does a specific date exist?

```python
userprovided.date.date_exists(2020, 2, 31)
# => False
```

### Normalize long form dates

Normalize German or English long form dates:

```python
userprovided.date.date_en_long_to_iso('October 3, 1990')
# => '1990-10-03'

userprovided.date.date_de_long_to_iso('3. Oktober 1990')
# => '1990-10-03'
```


## Validate Geographic Coordinates

Check if latitude and longitude values are within valid Earth ranges. This validates that coordinates are mathematically possible, not whether they point to land, sea, or a specific feature.

```python
userprovided.geo.is_valid_coordinates(48.8566, 2.3522)
# => True (Paris, France)

userprovided.geo.is_valid_coordinates(45, 181)
# => False (longitude out of range)

# Accepts strings that can be converted to numbers
userprovided.geo.is_valid_coordinates('51.5074', '-0.1278')
# => True (London, UK)
```


## Update and Deprecation Policy

* No breaking changes in micro-versions.
* It makes no sense to duplicate functionality already available in the Python Standard Library. Therefore, if this package contains functionality that becomes superseded by the Standard Library, it will start to log a deprecation warning. The functionality itself is planned to stay available for at least a major version of `userprovided` and as long as Python versions not containing this functionality are supported.
