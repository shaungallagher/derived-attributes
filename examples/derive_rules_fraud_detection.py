"""
This example file demonstrates a real-world problem that Derived Rules
can help solve.

PROBLEM

Imagine you are a credit card company that processes applications for
new accounts.  You want to establish a number of fraud checks and be
able to generate an internal fraud score so you can evaluate whether
an applications requires additional scrutiny.


SOLUTION

With Derived Rules, you and your fraud risk stakeholders can define the
rules in a simple Subject-Verb-Object format.  Perhaps they're comfortable
working in Excel.  They can manage the criteria there, then export their
spreadsheet as a CSV file.  The data submitted by the applicant can then
be evaluated against the Sentences defined in the CSV, producing Derived
Rules.  These rules can then be used to generate the internal fraud score.
"""

import csv
import io

from src.derived_attributes.derive import DeriveRules, InputBuilder


def derive_rules_fraud_detection():
    # Create a CSV.  Normally this would be done in a spreadsheet tool like Excel,
    # but for the purpose of this demo, we'll put together the data in a plaintext
    # format, then generate a CSV.
    fraud_rules = [
        {
            "attr": "_annual_income",
            "subject": "source",
            "verb": "parse",
            "object": "$.application.annual_income",
            "notes": "Applicant-supplied annual income",
        },
        {
            "attr": "overstated_income_risk",
            "subject": "_annual_income",
            "verb": ">",
            "object": 500000,
            "notes": "There is an increased risk the applicant overstated their income",
        },
        {
            "attr": "_provided_phone",
            "subject": "source",
            "verb": "parse",
            "object": "$.application.phone",
            "notes": "The phone number the applicant provided",
        },
        {
            "attr": "_verification_service_phone",
            "subject": "source",
            "verb": "parse",
            "object": "$.identity_verification_service.phone",
            "notes": "The phone number provided by the Identify Verification Service",
        },
        {
            "attr": "possibly_fraudulent_phone_number",
            "subject": "_provided_phone",
            "verb": "neq",
            "object": "_verification_service_phone",
            "notes": "Supplied phone number does not match Identity Verification Service data",
        },
        {
            "attr": "_provided_address",
            "subject": "source",
            "verb": "parse",
            "object": "$.application.address",
            "notes": "The address the applicant provided",
        },
        {
            "attr": "_verification_service_address",
            "subject": "source",
            "verb": "parse",
            "object": "$.identity_verification_service.address",
            "notes": "The address provided by the Identify Verification Service",
        },
        {
            "attr": "possibly_fraudulent_address",
            "subject": "_provided_address",
            "verb": "neq",
            "object": "_verification_service_address",
            "notes": "Supplied address does not match Identity Verification Service data",
        },
    ]

    # Create a StringIO object to hold the CSV data
    output = io.StringIO()

    # Write the dictionary to the StringIO object as CSV
    writer = csv.writer(output)

    # Write the header, minus the Notes field
    writer.writerow(["attr", "subject", "verb", "obj"])

    # Write the data
    for row in fraud_rules:
        writer.writerow([row["attr"], row["subject"], row["verb"], row["object"]])

    # Get the string value of the CSV
    fraud_rules_csv = output.getvalue()

    # Close the StringIO object
    output.close()

    # Get the customer purchase history.  Normally this would be fetched from
    # the database, but for the purpose of this demo, we'll construct it.
    application = {
        "application": {
            "annual_income": 800000,
            "phone": "555-555-1212",
            "address": "123 Main St.",
        },
        "identity_verification_service": {
            "phone": "555-555-9898",
            "address": "123 Main St.",
        },
    }

    # Construct Sentences from the CSV
    sentences = InputBuilder.from_csv(fraud_rules_csv)

    # Generate the Derived Attributes
    da = DeriveRules(sentences, application)
    derived_rules = da.derive()

    print("Expected output:")
    print("Failed 2 out of 3 fraud checks")

    # Output the results
    print("Derived Rules:")
    print(f"Failed {sum(derived_rules)} out of {len(derived_rules)} fraud checks")


if __name__ == "__main__":
    derive_rules_fraud_detection()
