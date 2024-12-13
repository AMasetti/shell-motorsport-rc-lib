from setuptools import setup, find_packages

setup(
    name="shell_motorsport",
    version="0.1.1",
    description="Control de Autos RC de Shell Motorsport a través de Bluetooth Low Energy (BLE)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Augusto Masetti",
    author_email="augmas15@gmail.com",
    url="https://github.com/AMasetti/shell-motorsport-rc-lib",
    packages=find_packages(),
    install_requires=[
        "bleak==0.21.1",
        "pybluez==0.23",
        "pycryptodome==3.19.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
