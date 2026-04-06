# TODO

## New Features

- [ ] **`is_wkn`** — Validate Wertpapierkennnummer (German 6-character security identifier) in `finance.py`
- [ ] **`is_iban`** — Validate International Bank Account Number (format + mod 97 check) in `finance.py`

## Security Findings

## Medium

- [x] **Document path traversal responsibility in `hashing.py:116`**
  Added docstring note that the caller is responsible for ensuring file_path points to an intended file.

- [x] **Strengthen deprecated hash algorithm check in `hashing.py:30-31`**
  The blocklist (`md5`, `sha1`, `md5-sha1`) can be bypassed via platform-specific aliases (e.g., `sha` for sha1). Fixed by adding post-construction check of `hashlib.new(hash_method).name` in both `calculate_file_hash` and `calculate_string_hash`.

## Low

- [x] **Fix `None` handling bug in `hashing.py:56-60`**
  If `hash_method` is `None`, `.strip()` raises `AttributeError` before the `None` check on line 59. The `None` guard is dead code.

- [ ] **Review user data in exception messages (`url.py:423,433`, `hashing.py:122`)**
  URLs and file paths are included in `ValueError` messages, which could leak to end users in calling applications.

- [x] **Add length limits for email validation (`mail.py`)**
  No maximum length check before regex matching. RFC 5321 limits email addresses to 254 characters.

- [x] **Add length limits for URL inputs (`url.py`)**
  Functions like `is_url()`, `normalize_url()`, `extract_domain()`, and `extract_tld()` accept strings of arbitrary length.

- [ ] **Evaluate email regex for ReDoS (`mail.py:18-25`)**
  Nested repetition in the domain part is a theoretical ReDoS concern. Anchors and restricted character classes mitigate practical risk, but a formal analysis would confirm safety.
