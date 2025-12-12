from setuptools import setup, find_packages

setup(
    name="omg-mitigation",
    version="0.1.0",
    description="O.MG Cable mitigation with rotating keymaps",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        'cryptography',
        'pyserial',
        # Add other dependencies from requirements.txt
    ],
)
