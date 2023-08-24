from setuptools import find_packages, setup

setup(
    name="yawms",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
)
