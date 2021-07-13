
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

dev_dependencies = [
    "pytest",
    "black",
    "pylint",
    "moto",
    "pdoc"
]


setuptools.setup(
    name="imurl",
    version="0.0.2",
    author="Travis Hesketh",
    author_email="travis@hesketh.scot",
    description="`imurl` is an immutable URL library, written in modern Python.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/thesketh/imurl",
    project_urls={
        "Bug Tracker": "https://github.com/thesketh/imurl/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries",
        "Typing :: Typed"
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.7",
    extras_require={"dev": dev_dependencies}
)