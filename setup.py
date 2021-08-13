import setuptools

from setuptools import find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = fh.read().splitlines()

with open("digital_thought_dfir/version", "r") as fh:
    version_info = fh.read()

setuptools.setup(
    name="digital_thought_dfir",
    version=version_info,
    author="Digital Thought",
    author_email="development@digital-thought.org",
    description="Digital Forensics & Incident Response Python Tools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Digital-Thought/dfir",
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta"
    ],
    packages=find_packages(exclude=('unit_tests', 'tests', 'docs', 'sampleConfigs')),
    python_requires='>=3.8',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'endpoint_report = digital_thought_dfir.reports.endpoints:main',
            'cbc_user_provision = digital_thought_dfir.edr.carbon_black.cloud.user_provision:main'
        ],
    }
)
