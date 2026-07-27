# Security Policy

## Reporting a vulnerability

**Do not use public issues or pull requests for security reports.**

Report privately: **[Report a vulnerability](https://github.com/RuedigerVoigt/userprovided/security/advisories/new)**
(or the *Security* tab → *Report a vulnerability*).

Please include the affected function, the version, and the input that triggers
the problem.

## Supported versions

Security fixes are always released as a new version. Only the most recent release
on PyPI is supported — there are no backports. As the package has no runtime
dependencies, upgrading is always the complete fix.

## Scope

Every security issue is in scope, except the following documented limitations:

* `hashing.calculate_string_hash` is documented as not a security primitive.
* `url.TWO_PART_TLDS` is a deliberate subset, not the Public Suffix List.
* `url.url_matches_domain` collapses all subdomains by design.
* `url.is_shortened_url` checks a finite list of services.
* `url.normalize_hostname` uses the Standard Library IDNA codec (IDNA 2003).
* `hashing.calculate_file_hash` leaves path traversal to the caller.

Improvements to these are welcome as ordinary issues or pull requests.
