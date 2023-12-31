# Derived Attributes
A Python library for applying computations to a JSON object using a Subject-Verb-Object grammar.<br><br>


## What does this library do, and why is it useful?

Suppose you have a large, complex JSON (or JSON-like) object.  Perhaps it represents one or more medical records, customer records, or financial records.

The object contains data that you want to work with, but not necessarily in its raw form.

It is common, in such a case, to pass the object through a processing layer or ETL job that parses the raw data and performs some operations on it to produce derived attributes, which are the data you actually care about.

For instance, if your JSON object contains a list of customer transactions, one useful derived value might be `average_order_value`.

This library provides a succint way of defining and computing these derived attributes.  (Essentially, the library becomes your processing layer.)  The derived attributes you define can be stored and managed in a variety of formats: in CSV files, in a database table, or in the codebase itself.


## Example

Suppose you have the following JSON-like object, which contains vendor expense data for multiple businesses:

```py
source = {
    "records": [
        {
            "business_name": "ABC Electronics",
            "vendors": [
                {
                    "vendor_name": "Tech Solutions",
                    "has_contract": False,
                    "budget": 15000,
                    "expenses": 8000,
                },
                {
                    "vendor_name": "Office Supplies Inc.",
                    "has_contract": True,
                    "budget": 2000,
                    "expenses": 1500,
                },
            ],
        },
        {
            "business_name": "XYZ Marketing",
            "vendors": [
                {
                    "vendor_name": "AdvertiseNow",
                    "has_contract": True,
                    "budget": 10000,
                    "expenses": 9000,
                },
                {
                    "vendor_name": "Print House",
                    "has_contract": True,
                    "budget": 3000,
                    "expenses": 3000,
                },
            ],
        },
    ]
}
```

Suppose you would like to derive the following attributes based on this data:

* `total_vendor_count`: The number of vendors across all businesses.
* `max_budget_only_contract`: The highest budget for vendors with a contract.
* `median_used_budget`: The median percentage of the monthly budget that has been used.

One approach to computing these derived values might be to normalize the data, create two-dimensional representations via database tables or data frames, then query and aggregate the data using tools like SQL or Pandas.

Derived Attributes allows you to instead work with the data in its JSON form, specifying the computions using a Subject-Verb-Object grammar that accepts JSONPath syntax:

| Attribute                      | Subject          | Verb               | Object                                                                |
| ------------------------------ | ---------------  | ------------------ | --------------------------------------------------------------------- |
| `total_vendor_count`           | `source`         | `parse_len`        | `$.records[*].vendors[*]`                                             |
| `max_budget_only_contract`     | `source`         | `parse_max`        | `$.records[*].vendors[?has_contract == true].budget`                  |
| `_used_budget`                 | `source`         | `parse_list`       | `$.records[*].vendors[*].expenses / $.records[*].vendors[*].budget`   |
| `median_used_budget`           | `_used_budget`   | `parse_median`     |                                                                       |

When these S-V-O sentences are evaluated, it produces the following derived attributes:

```py
{
    "total_vendor_count": 4,
    "max_budget_only_contract": 10000,
    "median_used_budget": 0.825,
}
```

Note: Attributes prefixed with an underscore are considered private and are useful for holding the results of intermediate calculations.  They are not returned.


## Subject-Verb-Object grammar

In the simple Subject-Verb-Object grammar this library uses:

* The Subject is a reference to a raw value (e.g. the source data), or to another derived attribute.

* The Verb is a unary or binary function to be performed against that value (e.g. an operator or aggregator).

* An optional Object value can be supplied as a second parameter to the Verb function.

Each S-V-O combination forms a simple sentence, the output of which is a Derived Attribute.

The grammar supports the ability to nest operations.  Each Derived Attribute can be used as inputs to other sentences.


## Supported Verbs

| Verb            | Definition                                                                                |
| --------------- | ----------------------------------------------------------------------------------------- |
| >               | Returns true if the Subject value is greater than the Object value; else false.           |
| <               | Returns true if the Subject value is less than the Object value; else false.              |
| =               | Returns true if the Subject value equals the Object value; else false.                    |
| eq              | Returns true if the (non-numeric) Subject value equals the Object value; else false.      |
| and             | Returns true if the Subject value and Object value are both truthy; else false.           |
| or              | Returns true if either the Subject or Object value is truthy; else false.                 |
| len             | Returns the length of a list provided as a Subject value.                                 |
| sum             | Returns the sum of a list of numeric values provided as a Subject value.                  |
| min             | Returns the minimum number in a list of numeric values provided as a Subject value.       |
| max             | Returns the maximum number in a list of numeric values provided as a Subject value.       |
| median          | Returns the median of a list of numeric values provided as a Subject value.               |
| parse           | Parse a JSONPath expression that matches a single scalar value, then return that value.   |
| parse_list      | Parse a JSONPath expression that matches a list of values, then return that list.         |
| parse_len       | Returns the number of values that match a JSONPath expression.                            |
| parse_sum       | Returns the sum of values that match a JSONPath expression.                               |
| parse_min       | Returns the minimum numeric value from all values that match a JSONPath expression.       |
| parse_max       | Returns the maximum numeric value from all values that match a JSONPath expression.       |
| parse_median    | Returns the median numeric value from all values that match a JSONPath expression.        |


## JSONPath syntax in Objects

The Derived Attributes library uses [jsonpath-ng](https://github.com/h2non/jsonpath-ng) to parse JSONPath expressions.

Please see that project's [JSONPath Syntax](https://github.com/h2non/jsonpath-ng) section for more details about how to construct these expressions.
