import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="imurl",
    version="0.1.3",
    author="Travis Hesketh",
    author_email="travis@hesketh.scot",
    description="`imurl` is an immutable URL library, written in modern Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thesketh/imurl",
    project_urls={
        "Bug Tracker": "https://github.com/thesketh/imurl/issues",
        "Documentation": "https://thesketh.github.io/imurl",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Typing :: Typed",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    package_data={"imurl": ["py.typed"]},
    python_requires=">=3.8",
)
