from setuptools import find_packages, setup

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="derived-attributes",
    version="0.2.0",
    author="Shaun Gallagher",
    author_email="github-shaun@pressbin.com",
    description="A Python library for applying computations to a JSON object using a Subject-Verb-Object grammar.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shaungallagher/derived-attributes",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "jsonata-python>=0.3.0",
        "jsonpath_ng>=1.5.3",
    ],
)
