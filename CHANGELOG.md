# Changelog / History

## Version 3.0.0 (2026-08-01)

* Breaking changes:
  * Dropped support for Python 3.10, which reaches EOL in October 2026. The minimum version is now 3.11.
  * `parameters`: `numeric_in_range`, `int_in_range` and `is_port` raise `TypeError` instead of `ValueError` when an argument has the wrong type in order to be consistent with the rest of the package.
  * `parameters`: `is_port` now rejects `bool`. `isinstance(True, int)` is `True`, so `is_port(True)` previously returned `True`, treating a flag as port 1.
  * `url`: `extract_domain`, `extract_tld` and `url_matches_domain` raise `TypeError` for non-string arguments.
* Security:
  * Added a [security policy](./SECURITY.md) and enabled private vulnerability reporting.
  * Publishing to PyPI now requires the tests, the coverage gate, and the linters to pass for the released commit.
  * Pinned `poetry` and `twine` to exact versions in the release workflow.
  * Bumped the pinned GitHub Actions to the latest versions.
  * All modules: user-provided values are now logged with `%r` and lazy `%`-arguments instead of `%s` or a pre-formatted f-string. `repr()` escapes newlines and control characters, so a crafted URL, dictionary key or bucket name can no longer forge additional log lines in the host application's log.
  * `hashing`: `calculate_file_hash` no longer skips verification when `expected_hash` is an empty string. Only `None` skips the check now, so a config field left blank can no longer turn "verify this file against a known hash" into "return success without verifying".
  * `hashing`: `calculate_file_hash` compares hashes with `hmac.compare_digest` instead of `!=`, so the comparison is constant-time.
  * `url`: `is_shortened_url` matched against the netloc, which carries the userinfo and the port. `https://bit.ly:443/x` and `https://evil.com@bit.ly/x` were therefore not recognized as shortened URLs, defeating the check that is meant to spot disguised link targets. It now matches on the hostname, like the rest of the module.
* New features:
  * `parameters`: added `strict_int` and `strict_numeric`, the strict counterparts to `int_in_range` and `numeric_in_range`.
  * `err`: added `HashMismatch` (subclass of `ValueError`), raised by `calculate_file_hash` when a file fails its hash check. Previously indistinguishable from the `ValueError` an unknown algorithm raises.
* Bug fixes:
  * `parameters`: `is_aws_s3_bucket_name` no longer rejects names that merely *start* like an IP address. AWS forbids a name "formatted as an IP address", so `1.2.3.45abc` is legal while `192.168.5.4` stays rejected.
  * `parameters`: `separated_string_to_set` rejects `sep='\'` instead of silently never splitting. The backslash escapes the next character, so it consumed every separator.
  * `parameters`: fixed the missing space in the `enforce_boolean` error message (`boolean,i.e`).
  * `hashing`: `calculate_file_hash` no longer raises an unrelated `TypeError` from `hmac.compare_digest` when `expected_hash` contains non-ASCII characters. Such a value cannot match a hexdigest and now counts as a mismatch. A non-string `expected_hash` raises `TypeError` with a clear message.
  * `url`: a trailing root-label dot (`www.example.com.`) no longer collapses a host onto its public suffix. `extract_domain(drop_subdomain=True)` returned `com.` instead of `example.com`, `extract_tld` returned `.` instead of `.com`, and `url_matches_domain` failed to match such a URL. Without `drop_subdomain` the host is still returned exactly as given.
  * `url`: `normalize_url` now collapses any run of slashes in the path, not just pairs. `str.replace` consumes non-overlapping matches, so a single pass turned `///a` into `//a` and left a duplicate behind. Two spellings of the same resource therefore produced two different results (`https://example.com//a` became `.../a`, while `https://example.com///a` became `.../​/a`), which defeats the purpose of a normalized URL used as an identity key.
  * `url`: `extract_domain` and `extract_tld` no longer fall back to the netloc when no hostname can be determined. The netloc carries the userinfo and the port, so `extract_domain('http://user:pass@')` returned the credentials as if they were a domain. Such input now raises `ValueError` (`extract_domain`) or returns an empty string (`extract_tld`).
  * `url`: `extract_tld` no longer swallows every exception. A URL that cannot be parsed still yields an empty string, but an unexpected error now reaches the caller instead of being reported as "no TLD found".
  * `url`: `is_url` no longer raises for URLs that `urllib.parse` cannot parse at all, such as an unclosed IPv6 literal (`http://[::1`). Such URLs are now simply invalid.
  * `url`: `is_url` now rejects a URL whose port is not a number or lies outside the range 0-65535. `urllib.parse` validates the port only on attribute access, so such a URL — which no client could ever dial — was reported as valid. Everything building on `is_url`, among them `normalize_url` and `is_shortened_url`, rejects those URLs as a result.
  * `url`: `normalize_url` raises its own `Malformed URL` message for an invalid port (`https://example.com:notaport`).
  * `hashing`: `calculate_file_hash` compares `expected_hash` case-insensitively and ignores surrounding whitespace.
* CI
  * The release workflow now verifies that the git tag matches the version in `pyproject.toml` before building, instead of failing at the upload step or publishing a mismatched version silently.


## Version 2.6.0 (2026-07-11)

* New features:
  * `url`: added `normalize_hostname` to reduce a bare hostname or IP literal to one canonical form (lowercased, trailing root-label dots removed, internationalized names converted to punycode, equivalent IPv4/IPv6 spellings canonicalized). Normalization is idempotent. Existing functions like `normalize_url` and `extract_domain` deliberately keep their behavior, as their outputs are identity keys in downstream databases.
  * `url`: added `extract_domain_from_host`, a host-level sibling of `extract_domain` for callers that already hold a bare hostname instead of a URL. It normalizes via `normalize_hostname` first and supports the same optional subdomain removal.
  * `parameters`: added `one_of` to check a string against a collection of allowed options. It validates and normalizes in one call: on a match it returns the member from the allowed collection (canonical spelling), matching case-insensitively by default after stripping whitespace. Unknown options raise `ValidationError` with the allowed options listed in sorted order; the optional `name`/`source` keywords produce a source-aware error message.
* Bug fixes:
  * `parameters`: `numeric_in_range` no longer accepts `NaN`. Since every comparison with `NaN` is `False`, it slipped through the range check and was returned as a valid in-range value. A `NaN` given value now returns the fallback; `NaN` as minimum, maximum, or fallback value raises `ValueError` (caller error). Infinite bounds (e.g. `math.inf` for "no upper limit") remain accepted.
* CI:
  * Bumped the pinned GitHub Actions to the latest versions.

## Version 2.5.0 (2026-06-14)

* New features:
  * `parameters`: added `parse_boolean` to convert the boolean spellings from config files, environment variables, and HTML forms (`1`/`yes`/`true`/`on` and `0`/`no`/`false`/`off`, case-insensitive and trimmed, mirroring `configparser.BOOLEAN_STATES`) into a real `bool`. Unrecognized values raise; the optional `name`/`source` keywords produce an actionable, source-aware error message.
  * `err`: added `ValidationError` (subclass of both `UserprovidedException` and `ValueError`) for strict validators that raise rather than fall back.
* Security fixes:
  * `url`: `is_url` no longer applies substring matching when a plain string is passed to `require_specific_schemes`. Previously `is_url('http://...', ('https'))` returned `True` because `('https')` is a string, not a tuple, and `'http' in 'https'` holds. A bare string is now treated as a single scheme name. The README example that demonstrated the string-instead-of-tuple pattern was corrected.
  * `ip`: `is_potential_ssrf_target` now flags the RFC 6598 carrier-grade NAT range (100.64.0.0/10). Python's `ipaddress` does not consider it private, so it previously slipped past the SSRF guard despite being a realistic internal target in cloud and carrier networks.
  * `mail`: `is_email` now logs the rejected address with `%r` instead of `%s`. A rejected address is attacker-controlled and may contain newlines or control characters; `repr()` escapes them and prevents log injection / forged log lines.
* Changed behavior:
  * String-validating predicates now share one contract: a non-string argument raises `TypeError`; a boolean is returned only for string input. This covers `finance.is_isin`/`is_iban` (previously returned `False` for non-strings), `url.is_url`/`is_shortened_url`, `parameters.is_aws_s3_bucket_name`, and `ip.is_loopback`/`is_private`/`is_link_local`/`is_potential_ssrf_target` (these previously raised an unhelpful `len()` error on `None`, yet returned `False` for some other non-strings). (`mail.is_email` already behaved this way.)
* Bug fixes:
  * `url`: `normalize_url` no longer corrupts URLs with IPv6 hosts. `urllib.parse` strips the square brackets from IPv6 literals and the reassembly did not restore them, so `http://[::1]:8080/path` became the invalid `http://::1:8080/path`.
* Tests:
  * Added IPv6 cases for `normalize_url`: brackets preserved, hex digits lowercased, standard port removal, non-standard port kept, query normalization.
  * Added scheme-restriction regression cases for `is_url` (plain string vs. tuple).
* CI:
  * Tooling: replaced flake8 with an enforcing ruff workflow (configured in `pyproject.toml`). The previous flake8 style pass ran with `--exit-zero` and could never fail CI; ruff enforces.
  * Tooling: added a Dependabot config to keep the GitHub Actions up to date automatically.
  * Security: pinned all GitHub Actions to full commit SHAs (with a version comment) instead of mutable tags, so a re-pointed upstream tag cannot inject code into the workflows — most importantly the PyPI publish job. Dependabot keeps the pins current.
  * Security: set least-privilege `permissions: contents: read` on the test, lint, and build workflows, so their `GITHUB_TOKEN` cannot write to the repository. The OIDC publishing capability (`id-token: write`) remains exclusive to the release workflow.
  * Security: Enabled release immutability.

## Version 2.4.0 (2026-06-06)

* New features:
  * `finance`: added `is_iban` to check whether a string has a valid IBAN format and ISO 7064 mod-97 checksum.
* Improvements:
  * `ip`: improved SSRF guard to detect alternate IP encodings (decimal integer, hex, old-style octal).
* Bug fixes:
  * Fixed documentation drift in README.
  * `parameters`: replaced `logging.exception` with `logging.error` outside except blocks.
  * `parameters`: `numeric_in_range` now rejects bool values.
* Tests:
  * Tests split into multiple files.
  * Enabled branch coverage.
* Tooling:
  * CI: coverage gate raised from 95% to 100% (enforced) to match the release standard.
  * CI: bumped GitHub Actions to current major versions.
  * CI: added Python 3.15 beta to the test matrices (ubuntu/windows/macOS/mypy) as a non-blocking, allow-prereleases job.

## Version 2.3.0 (2026-04-06)

* New features:
  * New module `ip`:
    * `is_loopback`: check whether a URL's host is a loopback address (127.0.0.0/8, ::1, localhost).
    * `is_private`: check whether a URL's host is a private address (RFC 1918, IPv6 unique-local fc00::/7).
    * `is_link_local`: check whether a URL's host is a link-local address (169.254.0.0/16, fe80::/10, .local hostnames).
    * `is_potential_ssrf_target`: preflight guard combining all three checks.
* Security fixes:
  * `mail`: enforce RFC 5321 length limits (254 chars total, 64 chars for local part) before regex matching.
  * `url`: reject strings exceeding 2048 characters in `is_url`, `extract_domain`, `extract_tld`, and `_host_from_url` (used by the `ip` module).
  * `url`: remove raw URL from `ValueError` messages in `extract_domain` to prevent log injection and XSS in calling applications.
* Bug fixes:
  * `hashing`: simplified convoluted `None`/empty guard in `hash_available` — replaced two-step conditional with a single clean check.

## Version 2.2.0 (2026-02-14)

* New features:
  * New module `finance`:
    * Function `is_isin` to check if a string has the correct format for an ISIN, including Luhn checksum verification.
  * `parameters`:
    * Added `clean_trim` function to strip whitespace and convert empty or whitespace-only strings to None or a custom value. Trivial, but often needed in web applications.
  * `hashing`:
    * Strengthened deprecated hash algorithm check: post-construction verification of canonical name catches platform-specific aliases that bypass the string blocklist.
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

* Tests now run with Python 3.10.

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
* The function `url.determine_file_extension` did not handle some edge cases separately, but instead suggested the extension `.unknown` in both cases. Now:
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

* New function `url.determine_file_extension` (moved here from the `exoskeleton` sister-project): determine the appropriate file extension either based on the URL and / or the mime type provided by the server.

## Version 0.7.0 beta (2020-06-25)

* New function `hash.calculate_file_hash` which calculates SHA224, SHA256, or SHA512 hashes for files.
* Extended documentation.

## Version 0.6.0 beta (2020-06-22)

* New function `parameters.convert_to_set`, which converts lists, strings, and tuples into sets. Moved here from the `exoskeleton` sister-project.
* New function `parameters.validate_dict_keys`, which checks if a dictionary contains only keys that are in a set of allowed / known keys. Furthermore it can check if a set of necessary keys is present.

## Version 0.5.5 beta (2020-06-15)

* Signal compatibility with [PEP 561](https://www.python.org/dev/peps/pep-0561/): If you type-check code that imports this package, tools like mypy now know that `userprovided` has type-hints and extend their checks to calls of these functions.

## Version 0.5.4 beta (2020-06-07)

* Improved error handling for date conversion.
* More tests.
* Clarify Update and Deprecation Policy.

## Version 0.5.3 beta (2020-04-18)

* Add function to check whether a port is within the valid range.

## Version 0.5.2 beta (2020-04-18)

* Add function to check for hash method availability, that raises ValueError for md5 and SHA1.

## Version 0.5.1 beta (2020-04-17)

* Add functions to analyze and convert dates.

## Version 0.5.0 beta (2020-04-17)

* The functions were previously part of the sister project exoskeleton. They were spun off, renamed and even more tests were added.
