# userprovided

![Supported Python Versions](https://img.shields.io/pypi/pyversions/userprovided)
![pypi version](https://img.shields.io/pypi/v/userprovided)
![Last commit](https://img.shields.io/github/last-commit/RuedigerVoigt/userprovided)
[![Downloads](https://pepy.tech/badge/userprovided)](https://pepy.tech/project/userprovided)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)

*"Never trust user input!"* is also true outside the security context: You cannot be sure users always provide you with valid and well-formatted data.
For a wide range of data, the Python package `userprovided`:
* checks for validity and plausibility
* normalizes input
* converts into standardized formats
* performs basic security checks

The code has type hints ([PEP 484](https://www.python.org/dev/peps/pep-0484/), using modern [PEP 604](https://peps.python.org/pep-0604/) `X | Y` syntax) and provides useful log and error messages.

Userprovided has functionality for the following inputs:
* [parameters](#handle-parameters):
  * [Tolerant vs. strict validators](#tolerant-vs-strict-validators): fall back to a default, or stop the program.
  * [Check a dictionary](#check-a-parameter-dictionary) for valid, needed, and unknown keys.
  * [Avoid keys without value in a dictionary](#avoid-keys-without-value-in-a-dictionary) to ensure all values are present.
  * [Convert into a set](#convert-into-a-set) from lists, strings and tuples.
  * [Parse separated strings into a set](#parse-separated-strings-into-a-set) with support for quotes and escaping.
  * [Check range of numbers and strings](#check-range-of-numbers-and-strings) to validate if values are in a specific range.
  * [Check integer range](#check-integer-range) with strict integer type enforcement.
  * [Clean and trim strings](#clean-and-trim-strings) by stripping whitespace and converting empty input to None or a custom value.
  * [Enforce boolean type](#enforce-boolean-type) to reject truthy/falsy values.
  * [Parse a boolean](#parse-a-boolean) from config/env/form spellings (yes/no/on/off/1/0) into a real `bool`.
  * [Check a string against allowed options](#check-a-string-against-allowed-options) and return the canonical spelling.
  * [Convert to an integer or fail](#convert-to-an-integer-or-fail) instead of silently using a default.
  * [Convert to a number or fail](#convert-to-a-number-or-fail) for values that may have decimals.
  * [Validate AWS S3 bucket names](#validate-aws-s3-bucket-names) against AWS naming rules.
* [url](#handle-urls):
  * [Normalize a URL](#normalize-urls) and drop specific keys from the query part of it.
  * [Normalize a hostname](#normalize-hostnames) to one canonical form (trailing dots, punycode, IPv6 spellings).
  * [Check](#check-urls) if a string is a URL.
  * [Check for shortened URLs](#check-for-shortened-urls) from known URL shortening services.
  * [Determine a file extension](#determine-a-file-extension) from a URL and the MIME-type sent by the server.
  * [Extract domain from URL](#extract-domain-from-url) with optional subdomain removal, supporting 2-part TLDs.
  * [Extract domain from a hostname](#extract-domain-from-a-hostname) for callers that already hold a bare hostname instead of a URL.
  * [Extract TLD from URL](#extract-tld-from-url) correctly identifying both standard and 2-part TLDs.
  * [Check if a URL belongs to a domain](#check-url-domain) with subdomain matching.
  * [Limits of the two-part TLD list](#limits-of-the-two-part-tld-list) and when to reach for a dedicated package.
* [ip](#check-ip-addresses):
  * [Check for loopback addresses](#check-for-loopback-addresses) (127.0.0.0/8, ::1, localhost).
  * [Check for private addresses](#check-for-private-addresses) (RFC 1918, IPv6 unique-local).
  * [Check for link-local addresses](#check-for-link-local-addresses) (169.254.0.0/16 incl. cloud metadata, fe80::/10, .local).
  * [Check for potential SSRF targets](#check-for-potential-ssrf-targets) combining all three checks.
* [hash](#hashes):
  * [Is the hash method available?](#check-hash-availability)
  * [Calculate a file hash](#calculate-a-file-hash) and (optionally) compare it to an expected value.
  * [Calculate a string hash](#calculate-string-hash) for non-security use cases like cache keys.
* [date](#handle-calendar-dates):
  * [Does a given date exist?](#check-date-existence)
  * Convert English and German [long format dates to ISO](#normalize-long-form-dates) strings.
* [mail](#check-email-addresses):
  * [Check if a string is a valid email address](#check-email-addresses).
* [finance](#finance):
  * [Validate ISIN](#validate-isin) (International Securities Identification Number).
  * [Validate IBAN](#validate-iban) (International Bank Account Number).
* [geo](#validate-geographic-coordinates):
  * [Validate coordinates](#validate-geographic-coordinates) to check if latitude and longitude are within valid Earth ranges.
* [err](#exceptions):
  * [The exceptions](#exceptions) this package raises and how to catch them.






## Installation

The recommended way is to install `userprovided` into a [virtual environment](https://docs.python.org/3/library/venv.html). This keeps it isolated from your system Python and avoids permission problems. (Do not use `sudo pip`: installing into the system Python as root can break packages managed by your operating system, and recent Linux distributions block it by default.)

On **Linux / macOS**:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install userprovided
```

On **Windows** (`py` is the [Python launcher](https://docs.python.org/3/using/windows.html#python-launcher-for-windows) that ships with the official Python installer):

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install userprovided
```

To upgrade to the latest version (with the virtual environment activated):

```bash
pip install userprovided --upgrade
```

## Tested and Used in Production

`userprovided` has 100% test coverage, no external dependencies, and is used in production by projects such as:

* [salted](https://github.com/RuedigerVoigt/salted) — a link checker and scraping tool
* [exoskeleton](https://github.com/RuedigerVoigt/exoskeleton) — a web scraping framework

## Handle Parameters

### Tolerant vs. Strict Validators

This module offers two families of validators. Picking the wrong one is the
difference between a program that keeps running with a silently substituted
value and one that stops with an actionable message.

| | Tolerant | Strict |
| --- | -------- | ------ |
| Functions | `numeric_in_range`, `int_in_range`, `string_in_range` | `strict_int`, `strict_numeric`, `parse_boolean`, `one_of` |
| Invalid value | logs at debug level, returns your fallback | raises `ValidationError` |
| Converts strings? | no, the value must already have the right type | yes — `'8'` becomes `8` |
| Error message | none, the caller never learns | names the value, the parameter and its origin |
| Use for | a pipeline that must not stop for one bad record | config files, environment variables, command line arguments |

Use the **tolerant** family when processing continues regardless: one
implausible value among thousands should not abort a scraping run.

Use the **strict** family at an application's input boundary. A mistyped
setting in a config file should stop the program at startup and say what to
fix — not silently run with a default the user did not choose.

```python
# Tolerant: out of range, so the fallback is returned and logged at debug.
userprovided.parameters.int_in_range('workers', 500, 1, 32, 4)
# => 4

# Strict: out of range, so it raises.
userprovided.parameters.strict_int('500', name='workers', minimum=1, maximum=32)
# => ValidationError: Invalid value '500' for workers - must be 32 or smaller.
```

Both families distinguish a bad *value* from a wrong *type*. A value a user
could plausibly have typed is a value problem: the strict validators raise
`ValidationError` (a subclass of `ValueError`), the tolerant ones fall back.
A wrong type — `None`, a list, a `bool` — always raises `TypeError`, in both
families, because that is a bug in the calling code rather than something an
end user can fix.

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
userprovided.parameters.keys_neither_none_nor_empty({'a': 123, 'b': 'example'})

# returns False:
userprovided.parameters.keys_neither_none_nor_empty({'a': '   ', 'b': 'example'})
userprovided.parameters.keys_neither_none_nor_empty({'a': None, 'b': 'example'})
userprovided.parameters.keys_neither_none_nor_empty({'a': list(), 'b': 'example'})
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
                     fallback_value) -> int | float



def string_in_range(string_to_check,
                    minimum_length,
                    maximum_length,
                    strip_string: bool = True) -> bool

userprovided.parameters.is_port(int)
# Checks if the port is integer and within the
# valid range from 0 to 65535. A non-integer — including a
# bool, which is a subclass of int — raises TypeError.
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
# => 1 (fallback value, logs at debug level)

# Rejects floats even if they represent whole numbers
userprovided.parameters.int_in_range(
    parameter_name='count',
    given_value=5.0,  # This is a float, not an int
    minimum_value=1,
    maximum_value=10,
    fallback_value=5
)
# => TypeError: Value must be an integer.
```

The function validates that minimum ≤ maximum and that the fallback value is within the allowed range.

### Clean and Trim Strings

Strip leading and trailing whitespace from strings. Empty or whitespace-only strings are converted to `None` by default, or to a custom value via the `empty_as` parameter. This is a trivial operation, but it is a repeating input normalization pattern in web applications: HTML forms submit empty fields as `''` rather than omitting them. Before storing form data in a database, empty strings should be converted to `None` so that the column is `NULL` instead of an empty string.

```python
userprovided.parameters.clean_trim('')
# => None

userprovided.parameters.clean_trim('   ')
# => None

userprovided.parameters.clean_trim('  hello  ')
# => 'hello'

userprovided.parameters.clean_trim(None)
# => None
```

**Parameters:**
- `value`: The input string or `None`.
- `empty_as`: The value to return when input is `None`, empty, or whitespace-only. Defaults to `None`. Set to `''` to keep empty strings, or use a custom placeholder.

```python
userprovided.parameters.clean_trim('', empty_as='N/A')
# => 'N/A'

userprovided.parameters.clean_trim('   ', empty_as='')
# => ''
```

**Raises:**
- `TypeError`: If `value` is not a string or `None`.

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

### Parse a Boolean

Where `enforce_boolean` rejects anything that is not already a `bool`, `parse_boolean` *converts* the boolean spellings delivered by config files, environment variables, and HTML forms into a real `bool`. It accepts `1` / `yes` / `true` / `on` (→ `True`) and `0` / `no` / `false` / `off` (→ `False`), case-insensitively and after trimming whitespace (mirroring `configparser.BOOLEAN_STATES`). Real booleans pass through unchanged. Unlike the tolerant helpers, it never falls back to a default — an unrecognized value raises `userprovided.err.ValidationError` (a subclass of `ValueError`).

```python
userprovided.parameters.parse_boolean('yes')      # => True
userprovided.parameters.parse_boolean('  Off  ')   # => False
userprovided.parameters.parse_boolean(True)        # => True

# Unrecognized values raise, with an actionable, source-aware message:
userprovided.parameters.parse_boolean(
    'nope', name='verbose', source='in config.ini')
# => ValidationError: Invalid value 'nope' for verbose in config.ini -
#    must be a boolean (true/false, yes/no, on/off, 1/0).
```

The optional `name` and `source` keywords are used only to build the error message, so a user learns *which* value to fix and *where*. A non-string, non-bool argument (e.g. `None`) raises `TypeError`.

### Check a String against Allowed Options

`one_of` checks that a string is one of a set of allowed options and returns the *member from the allowed collection* — so it validates and normalizes in one call: the caller gets the registered spelling, no matter how the user cased or padded the input. Matching is case-insensitive by default (set `case_sensitive=True` for exact matching); surrounding whitespace is always stripped. Like `parse_boolean`, it never falls back to a default — an unknown option raises `userprovided.err.ValidationError` (a subclass of `ValueError`) listing the allowed options in sorted order.

```python
userprovided.parameters.one_of(' html ', {'HTML', 'markdown'})
# => 'HTML' (the member from allowed, not the input spelling)

userprovided.parameters.one_of('Markdown', ('markdown', 'tex'))
# => 'markdown'

# Unknown options raise, with an actionable, source-aware message:
userprovided.parameters.one_of(
    'yaml', {'markdown', 'html', 'tex'},
    name='output_format', source='in config.ini')
# => ValidationError: Invalid value 'yaml' for output_format in config.ini -
#    must be one of: html, markdown, tex.
```

The optional `name` and `source` keywords are used only to build the error message. Caller mistakes raise immediately instead of failing validation: an empty `allowed` collection or one whose members differ only in case (ambiguous under case-insensitive matching) raises `ValueError`; a non-string value or non-string members raise `TypeError`.

### Convert to an Integer or Fail

`strict_int` converts a value to an `int` or raises — the strict counterpart to
`int_in_range`. Strings are stripped before conversion, so `' 8 '` is valid.

```python
userprovided.parameters.strict_int('8')
# => 8

userprovided.parameters.strict_int('8', name='workers', minimum=1, maximum=32)
# => 8 (bounds are inclusive)

# Floats are rejected instead of truncated, because truncation hides typos:
userprovided.parameters.strict_int('5.5', name='workers', source='in config.ini')
# => ValidationError: Invalid value '5.5' for workers in config.ini -
#    must be a whole number.

# A bool is never a count, even though bool is a subclass of int:
userprovided.parameters.strict_int(True)
# => TypeError: strict_int expects an int or a string, not a bool.
```

### Convert to a Number or Fail

`strict_numeric` is the same for values that may have decimals, and the strict
counterpart to `numeric_in_range`. It always returns a `float`, even for `int`
input — use `strict_int` when you need an `int`.

```python
userprovided.parameters.strict_numeric('2.5', name='timeout', minimum=0.0)
# => 2.5

userprovided.parameters.strict_numeric(3)
# => 3.0 (always a float)

# NaN and infinity are rejected: every comparison with NaN is False, so a NaN
# would pass any range check unnoticed.
userprovided.parameters.strict_numeric('nan', name='timeout')
# => ValidationError: Invalid value 'nan' for timeout - must be a finite number.
```

For both functions the optional `name` and `source` keywords only build the
error message, so the user learns *which* value to fix and *where*. A `NaN`
bound raises `ValueError` and a `minimum` larger than the `maximum` raises
`ContradictoryParameters`: those are caller mistakes, not bad input.

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
- Cannot contain consecutive dots (..)
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
  * drop any embedded credentials (`user:password@`),
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

### Normalize Hostnames

Different spellings of the same host — a trailing root-label dot (`example.com.`), an internationalized name versus its punycode form (`münchen.example` vs. `xn--mnchen-3ya.example`), or equivalent IPv6 literals (`::1` vs. `0:0:0:0:0:0:0:1`) — all identify the same machine. `normalize_hostname` reduces a bare hostname or IP literal (not a URL) to one canonical form, suitable as an identity key for tasks like rate limiting or deduplication. Normalization is idempotent: feeding the result back in returns it unchanged.

Note that `normalize_url` deliberately does *not* canonicalize hosts this way, as its output serves as an identity key in existing downstream databases.

```python
userprovided.url.normalize_hostname('Example.COM.')
# => 'example.com'

# Internationalized names are canonicalized to punycode
# (stdlib IDNA codec, i.e. IDNA 2003):
userprovided.url.normalize_hostname('MÜNCHEN.example')
# => 'xn--mnchen-3ya.example'

# Equivalent IP spellings converge; IPv6 is accepted with or
# without brackets and returned without them:
userprovided.url.normalize_hostname('[0:0:0:0:0:0:0:1]')
# => '::1'

userprovided.url.normalize_hostname('2001:DB8::1')
# => '2001:db8::1'
```

A non-string raises `TypeError`; empty input and input longer than 2048 characters raise `ValueError`. Everything else is normalized best-effort — this is a normalizer, not a validator.

### Check URLs

To check whether a string is a valid URL - including a scheme (like `https`) - use `userprovided.url.is_url`. 

```python
userprovided.url.is_url('https://www.example.com')
# => True
userprovided.url.is_url('www.example.com')
# => False
```

You can insist on specific schemes:

```python
userprovided.url.is_url('https://www.example.com', ('ftp',))
# => False (Schema is not permitted)

userprovided.url.is_url('ftp://www.example.com', ('ftp',))
# => True
```

Note the trailing comma: `('ftp',)` is a tuple, while `('ftp')` is just the string `'ftp'`. A single scheme may also be passed as a plain string, e.g. `'https'`.

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

Note that `extract_domain` deliberately does *not* canonicalize the host (trailing dots, punycode, IPv6 spellings stay as given), as its output serves as an identity key in existing downstream databases. If you hold a bare hostname and want a canonical form, use `extract_domain_from_host`.

The one exception is `drop_subdomain=True`: there the trailing root-label dot of a fully qualified name is removed, because the registrable domain is a derived key and `example.com.` must not become a second key for `example.com`.

```python
userprovided.url.extract_domain('https://www.example.com.')
# => 'www.example.com.' (host returned exactly as given)

userprovided.url.extract_domain('https://www.example.com.', drop_subdomain=True)
# => 'example.com'
```

### Extract Domain from a Hostname

`extract_domain_from_host` is the host-level sibling of `extract_domain` for callers that already hold a bare hostname and would otherwise have to fabricate a URL around it. Unlike `extract_domain`, it normalizes its input via `normalize_hostname` first (trailing dot, punycode, IP canonicalization).

```python
userprovided.url.extract_domain_from_host('www.example.co.uk', drop_subdomain=True)
# => 'example.co.uk'

userprovided.url.extract_domain_from_host('MÜNCHEN.example.')
# => 'xn--mnchen-3ya.example'

# IP literals have no subdomains or public suffix and are
# returned in canonical form regardless of drop_subdomain:
userprovided.url.extract_domain_from_host('[::1]', drop_subdomain=True)
# => '::1'
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

### Check URL Domain

Check if a URL belongs to a specific domain, with subdomain matching. All subdomains (including `www.`) are resolved to the registrable domain before comparison. This means `www.example.com`, `sub.example.com`, and `example.com` all match `example.com`. Correctly handles 2-part TLDs like `.co.uk`.

Note: Because all subdomains are collapsed to the registrable domain, this function cannot distinguish `www.example.com` from `sub.example.com`. If you need to match a specific subdomain, use `extract_domain` directly and compare the full hostname.

```python
userprovided.url.url_matches_domain('https://en.wikipedia.org/wiki/Test', 'wikipedia.org')
# => True

userprovided.url.url_matches_domain('https://www.example.co.uk/page', 'example.co.uk')
# => True

userprovided.url.url_matches_domain('https://evil.com', 'wikipedia.org')
# => False
```

### Limits of the Two-Part TLD List

`extract_domain(drop_subdomain=True)`, `extract_tld` and `url_matches_domain`
all resolve a hostname to its *registrable domain*, which requires knowing
where the public suffix ends. Doing that correctly means consulting the
[Public Suffix List](https://publicsuffix.org/) — several thousand rules,
updated continuously. This package relies solely on the Python Standard
Library, so it instead carries a hand-maintained set of the most common
two-part suffixes (`userprovided.url.TWO_PART_TLDS`, currently 98 entries
covering 20 countries).

Under a suffix that is **not** in that set, one label too few is kept:

```python
# .co.uk is in the list:
userprovided.url.extract_domain('https://www.alice.co.uk', drop_subdomain=True)
# => 'alice.co.uk'

# .com.ua is not:
userprovided.url.extract_domain('https://www.alice.com.ua', drop_subdomain=True)
# => 'com.ua'   (not 'alice.com.ua')
```

Two consequences follow, and the second one matters for security:

```python
# 1. Matching your own site fails under an unlisted suffix:
userprovided.url.url_matches_domain('https://www.alice.com.ua/p', 'alice.com.ua')
# => False

# 2. Unrelated sites share one registrable domain, so never derive the
#    expected domain with the same function — pass a literal instead:
expected = userprovided.url.extract_domain('https://alice.com.ua', drop_subdomain=True)
# => 'com.ua'
userprovided.url.url_matches_domain('https://bob.com.ua/p', expected)
# => True — bob is not alice
```

If your application needs full public-suffix coverage, use a dedicated package
such as [tldextract](https://pypi.org/project/tldextract/), which ships and
updates the Public Suffix List. That is a dependency for your application to
take; `userprovided` will not take it.

## Check IP Addresses

These functions extract the host from a URL and check its IP address properties. They do **not** perform DNS resolution — hostnames that are not IP addresses are only matched by name (e.g., `localhost`, `.local`).

### Check for Loopback Addresses

Returns `True` for IPv4 loopback (`127.0.0.0/8`), IPv6 loopback (`::1`), and the hostname `localhost`.

```python
userprovided.ip.is_loopback('http://127.0.0.1/')    # => True
userprovided.ip.is_loopback('http://localhost/')     # => True
userprovided.ip.is_loopback('https://example.com/') # => False
```

### Check for Private Addresses

Returns `True` for RFC 1918 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) and IPv6 unique-local (`fc00::/7`).

```python
userprovided.ip.is_private('http://192.168.1.1/')   # => True
userprovided.ip.is_private('http://8.8.8.8/')       # => False
```

### Check for Link-Local Addresses

Returns `True` for IPv4 link-local (`169.254.0.0/16`, including the cloud metadata endpoint `169.254.169.254`), IPv6 link-local (`fe80::/10`), and hostnames ending with `.local` (mDNS).

```python
userprovided.ip.is_link_local('http://169.254.169.254/')  # => True (AWS/GCP/Azure metadata)
userprovided.ip.is_link_local('http://myprinter.local/')  # => True
userprovided.ip.is_link_local('https://example.com/')     # => False
```

### Check for Potential SSRF Targets

Combines `is_loopback`, `is_private`, and `is_link_local`. Use this as a preflight guard before fetching a user-supplied URL.

```python
userprovided.ip.is_potential_ssrf_target('http://169.254.169.254/') # => True
userprovided.ip.is_potential_ssrf_target('http://192.168.1.1/')     # => True
userprovided.ip.is_potential_ssrf_target('https://example.com/')    # => False

userprovided.ip.is_potential_ssrf_target('http://[::1')             # => True
# => a URL with no determinable host is reported as a target, so a
#    malformed URL is refused instead of fetched
```

Unlike `is_loopback`, `is_private` and `is_link_local`, which describe a host and return `False` for a URL without one, this function is a guard: it answers `True` whenever it cannot determine the host.

## Finance

### Validate ISIN

Check if a string has the correct format for an International Securities Identification Number (ISO 6166). An ISIN has 12 characters: a 2-letter country code, 9 alphanumeric characters, and a Luhn check digit. This validates the format and checksum, but does not verify the ISIN is actually registered. Accepts both upper and lowercase input.

```python
userprovided.finance.is_isin('DE0007236101')
# => True (Siemens)

userprovided.finance.is_isin('US5949181045')
# => True (Microsoft)

userprovided.finance.is_isin('INVALID')
# => False
```

### Validate IBAN

Check if a string has the format of a valid International Bank Account Number (ISO 13616). This validates the structure (2-letter country code, 2 check digits, alphanumeric BBAN) and the ISO 7064 mod-97 checksum. Accepts both upper and lowercase input as well as the printed format with spaces.

This only checks the format and checksum. It does **not** verify that the IBAN belongs to a real, open account. It also does not check the country-specific length (so a checksum-valid number with the wrong length for its country is not rejected) nor the country-specific BBAN structure — for those you need a bank-data provider or per-country rules.

```python
userprovided.finance.is_iban('DE89370400440532013000')
# => True

userprovided.finance.is_iban('DE89 3704 0044 0532 0130 00')
# => True (printed format with spaces accepted)

userprovided.finance.is_iban('DE89370400440532013001')
# => False (wrong checksum)
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
print(userprovided.hashing.hash_available('md5'))
# => DeprecatedHashAlgorithm exception because md5 is deprecated

print(userprovided.hashing.hash_available('sha256'))
# => True on almost any system
```

### Calculate a file hash

You can calculate hash sums for files. If you do not provide the method, this defaults to `SHA256`. Other supported methods are `SHA224` and `SHA512`.

```python
# returns the hash of the file as a string:
userprovided.hashing.calculate_file_hash(pathlib.Path('./foo.txt'))
```

If you provide an expected value for the hash you can check for file changes or tampering. In the case the provided value and the calculated hash do *not* match, a `userprovided.err.HashMismatch` exception is raised.

```python
userprovided.hashing.calculate_file_hash(
    file_path = pathlib.Path('./foo.txt'),
    hash_method = 'sha512',
    expected_hash = 'not_the_right_value')
# => raises HashMismatch
```

The comparison ignores case and surrounding whitespace, and runs in constant time. Only `None` skips the check — an empty string is a value that cannot match, not a request to skip verification.

`HashMismatch` is a subclass of `ValueError`, so existing handlers keep working. Catch it specifically to tell a failed integrity check apart from a configuration error like an unknown algorithm name, which stays a plain `ValueError`:

```python
try:
    userprovided.hashing.calculate_file_hash(path, 'sha256', expected)
except userprovided.err.HashMismatch:
    print('The file does not match its expected hash - do not trust it.')
except ValueError:
    print('The hash method is misconfigured.')
```

### Calculate String Hash

Compute a deterministic hash of string data for non-security use cases such as fingerprints, cache keys, or content de-duplication.

```python
userprovided.hashing.calculate_string_hash('example data')
# => returns the SHA256 hash as a string

userprovided.hashing.calculate_string_hash('example data', hash_method='sha512')
# => returns the SHA512 hash as a string

userprovided.hashing.calculate_string_hash('example data', encoding='utf-8')
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


## Exceptions

The `userprovided.err` module defines the exceptions this package raises:

| Exception | Also inherits from | Raised when |
| --------- | ------------------ | ----------- |
| `UserprovidedException` | — | Base class. Never raised directly. |
| `ValidationError` | `ValueError` | A [strict validator](#tolerant-vs-strict-validators) rejects a user-supplied value instead of falling back to a default. |
| `ContradictoryParameters` | `ValueError` | Parameters contradict each other, like dropping query keys while leaving the query part unchanged. |
| `QueryKeyConflict` | — | A URL query part repeats a key with conflicting values. |
| `DeprecatedHashAlgorithm` | — | MD5 or SHA1 was requested, even if available on the system. |
| `HashMismatch` | `ValueError` | A file's hash does not match the expected value. |

Every exception inherits from `UserprovidedException`, so one handler catches
everything this package raises:

```python
try:
    userprovided.parameters.one_of(user_input, {'html', 'markdown'})
except userprovided.err.UserprovidedException as e:
    print(f'userprovided rejected the input: {e}')
```

`ValidationError`, `ContradictoryParameters` and `HashMismatch` additionally
inherit from `ValueError`, so existing handlers keep working and you can stay
unaware of this package's own exception classes:

```python
try:
    userprovided.parameters.parse_boolean(config['verbose'], name='verbose')
except ValueError as e:
    # Catches ValidationError without importing userprovided.err
    print(f'Bad configuration value: {e}')
```

Note that not every error is a custom exception: wrong *types* raise the builtin
`TypeError`, and some functions raise a plain `ValueError`.

## Update and Deprecation Policy

* No breaking changes in micro-versions.
* It makes no sense to duplicate functionality already available in the Python Standard Library. Therefore, if this package contains functionality that becomes superseded by the Standard Library, it will start to log a deprecation warning. The functionality itself is planned to stay available for at least a major version of `userprovided` and as long as Python versions not containing this functionality are supported.
