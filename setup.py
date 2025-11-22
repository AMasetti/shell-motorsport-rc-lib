"""Setup configuration for Shell Motorsport RC Car library."""
from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="shell_motorsport",
    version="0.2.0",
    description="Control de Autos RC de Shell Motorsport a través de Bluetooth Low Energy (BLE)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Augusto Masetti",
    author_email="augmas15@gmail.com",
    url="https://github.com/AMasetti/shell-motorsport-rc-lib",
    packages=find_packages(),
    install_requires=[
        "bleak>=0.21.1",
        "pycryptodome>=3.19.0",
    ],
    extras_require={
        "joycon": [
            "joycon-python>=0.1.0",
            "hidapi>=0.14.0",
            "pyglm>=2.7.0",
        ],
        "dev": [
            "pytest>=8.3.4",
            "pytest-asyncio>=0.24.0",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Topic :: System :: Hardware",
    ],
    keywords="rc car bluetooth ble motorsport shell",
)
