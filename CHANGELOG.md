# Changelog / History

## Version 2.2.0 (unreleased)

* New features:
  * New module `finance`:
    * Function `is_isin` to check if a string has the correct format for an ISIN, including Luhn checksum verification.
  * `url`:
    * Added `url_matches_domain` function to check if a URL belongs to a specific domain, with subdomain matching.

## Version 2.1.1 (2025-11-02)

* New features:
  * `parameters`:
    * Added `separated_string_to_set` function to parse separated strings (CSV-like) into a set.
      * Supports custom separators (default: comma).
      * Quote support to include separators within fields.
      * Backslash escaping for special characters.
      * Automatic whitespace trimming and empty field removal.
      * Returns None for None input, empty set for empty string.
      * Comprehensive validation with helpful error messages.

## Version 2.1.0 (2025-11-01)

* New features:
  * `url`:
    * Added `extract_domain` function to extract the domain (hostname) from a URL.
      * Supports optional `drop_subdomain` parameter to extract only the registrable domain (e.g., `example.co.uk` from `www.subdomain.example.co.uk`).
      * Correctly handles many 2-part TLDs (country code second-level domains) such as `.co.uk`, `.com.au`, `.co.jp`, etc.
      * Properly handles edge cases: IPv4 addresses, IPv6 addresses, localhost, and single-word domains are returned unchanged.
      * Case-insensitive domain normalization (returns lowercase).
    * Added `extract_tld` function to extract just the TLD from a URL.
      * Returns 2-part TLDs as a single unit (e.g., `.co.uk`, `.com.au`).
      * Returns empty string for IP addresses, localhost, or single-word domains.
      * Includes leading dot in the result (e.g., `.com`, `.co.uk`).


## Version 2.0.0 (2025-10-28)

* Supported Python versions:
  * Dropped support for Python 3.8 and 3.9 (EOL).
  * Added support for Python 3.13 and 3.14.
* Contributing Guidelines:
  * Added [CONTRIBUTING.md](./CONTRIBUTING.md).
  * Added [AGENTS.md](./AGENTS.md) file that defines rules and guidelines for software agents.
  * Add a Pull Request template.
* Packaging:
  * Replaced `setup.py` with a `pyproject.toml` managed by Poetry.
* Security:
  * Security linter: Added [bandit](https://github.com/PyCQA/bandit) workflow.
  * Publish to PyPI with a [Trusted Publisher / OIDC](https://docs.pypi.org/trusted-publishers/).
* Quality:
  * Converted all docstrings to Google format.
  * Ensure with an automatic workflow that coverage is 95% or higher.
* New Features and bug fixes:
  * `date`:
    * parse more ordinal suffixes (1st, 2nd, 3rd, 4th) in `date_en_long_to_iso`
  * `geo`:
    * new module
    * `is_valid_coordinates` checks if coordinates are possible i.e. within possible Earth ranges
  * `hashing`:
    * Added `calculate_string_hash` function for basic hashing of string data. This method is not advanced enough in a security context.
    * Added `_hash_is_deprecated` helper function to centralize deprecated algorithm checking.
    * Bugfix in `calculate_file_hash`: prevent memory exhaustion by reading file in chunks. Support more methods.
  * `mail`:
    * Extend check / RegEx for email validation
  * `parameters`:
    * Fix typo in parameter name: `maximum_lenght` → `maximum_length`.
    * `is_port`: port 0 was incorrectly excluded.
    * Fix parameter name logic in `enforce_boolean`.
    * Catch more errors in `is_aws_s3_bucket_name`.
  * `url`:
    * Added `is_shortened_url` which checks if an URL is a short link by comparing it to a list of popular services. (Currently 24 domains recognized)
    * Renamed `normalize_query_part` to `_normalize_query_part` to mark it as an internal helper function.
* Other:
  * Changed all severity levels of logging messages from error / warning to debug. The package must not spam the logs of the application using it.


## Version 1.0.0 (2023-10-10)

* Dropped support for Python 3.6 and 3.7 due to EOL of these versions.
* Added support and tests for Python 3.11 and the recently released 3.12.
* Breaking Changes:
  * Methods in `userprovided.hash` have been moved to `userprovided.hashing` with version 0.9.1. Now the mitigation has been removed and calling the old method will fail instead of raising a deprecation warning.
* No functional changes.

## Version 0.9.4 (2021-10-06)

* Test now run with Python 3.10.

## Version 0.9.3 (2021-08-05)

* Marked as compatible with Python 3.10 as tests with release candidate 1 run flawlessly on Linux, MacOS, and Windows.

## Version 0.9.2 (2021-07-15)

* Introduced custom exceptions to allow precise handling:
  * `userprovided.err.QueryKeyConflict` is thrown by `url.normalize_query_part` if there is a duplicate key in the query part with a different value. As some sites (like `nytimes.com`) use multiple keys with the same name, the method got an extra parameter `do_not_change_query_part` (default: False) to keep the query part unchanged if so needed.
  * `userprovided.err.DeprecatedHashAlgorithm` is thrown, if the user tries to use the `MD5` or `SHA1` hashing algorithm.
  * `userprovided.err.ContradictoryParameters` is thrown if a user calls a method with settings that contradict each other.

## Version 0.9.1 (2021-06-15)

* New method `parameters.keys_neither_none_nor_empty` takes a dictionary and returns `False` if the value of any key is None, an empty string, or an empty iterable (of the kind dict/list/set/str/tuple).
* Reached 100% test coverage.
* **Methods in `userprovided.hash` have been moved to `userprovided.hashing`** in order to avoid redefining the builtin `hash` object. *The old paths will work until version 1.0.0 of userprovided!* However, they will yield a deprecation warning from now on.

## Version 0.9.0 (2021-05-17)

* The new function `date.date_de_long_to_iso` takes a long format German date (like '3. Oktober 1990') and returns a standardized date string (i.e. YYYY-MM-DD).
* The functions `url.normalize_url()` and `url.normalize_query_part()` now have the optional parameter `drop_key` which accepts a list of keys, that are then removed from the query part of the URL. This allows you (for example) to remove session-ids or trackers.
* The function `hash.calculate_file_hash()` now has the optional parameter `expected_hash` which allows you to compare the calculated file hash to the hash value you expect in order to detect changes or tampering.
* **Breaking Changes**:
    * The function `port.port_in_range()` is replaced by `parameters.is_port()`.
    * The function `cloud.is_aws_s3_bucket_name()` is replaced by `parameters.is_aws_s3_bucket_name()`.

## Version 0.8.1 (2021-03-11)

* Set PyPI development status to `stable`.
* Switched from `unittest` to `pytest` and improved test coverage.
* No functional changes.
* Improved documentation.

## Version 0.8.0 beta (2020-11-15)

* The method `hash.calculate_file_hash` now also accepts a string for the `file_path` parameter instead of only a `pathlib.Path` object as before.
* The method `url.is_url` does not log an error anymore if the URL is malformed. Other methods use `is_url` for checks and this would pollute the logs. Instead those messages have been downgraded to `debug`. However, if the requirement for a specific scheme is not met, there will be still an error logged.
* The method `url.normalize_query_part` does raise `ValueError` if it is given a full URL instead of the query part.
* Currently 98% test coverage.

Bugfixes:
* The function `url.determine_file_extension` did not handle some edge cases separetly, but instead suggested the extension `.unknown` in both cases. Now:
    * If neither the URL nor the server provide enough information to determine the file extension, the function will suggest `.unknown`.
    * If the file extension in the URL and the provided mime-type contradict each other, the file extension suggested by the URL will prevail.
* The function `url.determine_file_extension` did try to guess a file extension from the URL even if that missed the path part (i.e. `https://www.example.com` instead of something like `https://www.example.com/index.html`). Now it only guesses from the URL if there is a path component. Otherwise only the mime-type suggested by the server will be used.
* The method `url.normalize_query_part` does not raise an exception anymore, if a chunk of the query part is malformed by missing an equal sign (like `example.com/index.php?missinghere&foo=bar`).
* Fix `calculate_file_hash` (missing value for check).

## Version 0.7.6 beta (2020-11-03)

Bugfixes:
* The functions `url.normalize_url` (respectively `normalize_query_part`) no longer throw an exception if confronted with a not RFC 3986 compliant URL which does not use key=value syntax in the query part. Such URLs are for example generated by some versions of vBulletin.
* `url.py` contained a print statement used for debugging.

## Version 0.7.5 beta (2020-10-27)

* New function `url.normalize_url` which normalizes an URL:
    * remove whitespace around it,
    * convert scheme and hostname to lowercase,
    * remove ports if they are the standard port for the scheme,
    * remove duplicate slashes from the path,
    * remove fragments (like #foo),
    * remove empty elements of the query part,
    * order the elements in the query part by alphabet

## Version 0.7.4 beta (2020-10-11)

* All tests are now also run with Python 3.9.

## Version 0.7.3 beta (2020-07-10)

* New function `parameters.string_in_range`: Strips whitespace from both ends of a string and then checks if the length of that string falls in given limits.
* New function `parameters.enforce_boolean`: Raises a ValueError if the parameter is not of type bool.

## Version 0.7.2 beta (2020-07-09)

* New function `parameters.numeric_in_range`: checks if a given number is between a minimum and a maximum value. If not it returns a fallback value.
* New function `parameters.int_in_range` as a special case of `parameters.numeric_in_range`

## Version 0.7.1 beta (2020-07-09)

* New function `url.determine_file_extension` (moved here from the `exoskeleton` sister project): determine the appropriate file extension either based on the URL and / or the mime type provided by the server.

## Version 0.7.0 beta (2020-06-25)

* New function `hash.calculate_file_hash` which calculates SHA224, SHA256, or SHA256 hashes for files.
* Extended documentation.

## Version 0.6.0 beta (2020-06-22)

* New function `parameters.convert_to_set`, which converts lists, strings, and tuples into sets. Moved here from the `exoskeleton` sister-project.
* New function `parameters.validate_dict_keys`, which checks if a dictionary contains only keys that are in a set of allowed / known keys. Furthermore it can check if a set of necessary keys is present.

## Version 0.5.5 beta (2020-06-15)

* Signal compatibility with [PEP 561](https://www.python.org/dev/peps/pep-0561/): If you type-check code that imports this package, tools like mypy now know that `userprovided` has type-hints and extend their checks to calls of these functions.

## Version 0.5.4 beta (2020-06-07)

* Improved error handling for date conversion.
* More tests.
* Clarify Update and Deprecation Policy

## Version 0.5.3 beta (2020-04-18)

* Add function to check whether a port is within the valid range.

## Version 0.5.2 beta (2020-04-18)

* Add function to check for hash method availability, that raises ValueError for md5 and SHA1.

## Version 0.5.1 beta (2020-04-17)

* Add functions to analyze and convert dates.

## Version 0.5.0 beta (2020-04-17)

* The functions were previously part of the sister project exoskeleton. They were spun off, renamed and even more tests were added.
