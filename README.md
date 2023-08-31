# derived-attributes
A Python library for computing derived attributes from a JSON object.


# What does this library do, and why is it useful?

Suppose you have a large, complex JSON (or JSON-like) object.  Perhaps it represents one or more medical records or financial records.

The object contains data that you want to work with, but not necessarily in its raw form.

It is common, in such a case, to pass the object through a processing layer that parses the raw data and performs some operations on it to produce derived attributes, which is the data you actually care about.

For instance, if your JSON object contains, among other things, a list of vendor expenses, one useful derived value might be `average_expense`.  Another might be `vendor_count`.

This library provides a succint way of defining and computing these derived values.







