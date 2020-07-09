# Changelog / History

## version 0.7.1 beta (2020-07-09)

* New function `url.determine_file_extension()` (moved here from the `exoskeleton` sister project): determine the appropiate file extension either based on the URL and / or the mime type provided by the server.

## version 0.7.0 beta (2020-06-25)

* New function `hash.calculate_file_hash` which calculates SHA224, SHA256, or SHA256 hashes for files.
* Extended documentation.

## version 0.6.0 beta (2020-06-22)

* New function `parameters.convert_to_set`, which converts lists, strings, and tuples into sets. Moved here from the `exoskeleton` sister-project.
* New function `parameters.validate_dict_keys`, which checks if a dictionary contains only keys that are in a set of allowed / known keys. Furthermore it can check if a set of necessary keys is present.

## version 0.5.5 beta (2020-06-15)

* Signal compatibility with [PEP 561](https://www.python.org/dev/peps/pep-0561/): If you type-check code that imports this package, tools like mypy now know that `userprovided` has type-hints and extend their checks to calls of these functions.

## version 0.5.4 beta (2020-06-07)

* Improved error handling for date conversion.
* More tests.
* Clarify Update and Deprecation Policy

## version 0.5.3 beta (2019-04-18)

* Add function to check whether a port is within the valid range.

## version 0.5.2 beta (2019-04-18)

* Add function to check for hash method availability, that raises ValueError for md5 and sha1.

## version 0.5.1 beta (2019-04-17)

* Add functions to analyze and convert dates.

## version 0.5.0 beta (2019-04-17)

* The functions were previously part of the sister project exoskelton. They were spun off, renamed and even more tests were added.
