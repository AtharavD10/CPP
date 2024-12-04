from setuptools import setup, find_packages

setup(
    name='MobileSalesTracker',  # Unique name for your library
    version='0.1.0',           # Version of your library
    author='Atharav Deshpande',
    author_email='atharavd10@gmail.com',
    description='We have created this library to fetch and analyze the order details which is useful for the tracker admin',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/AtharavD10/CPPLibrary.git',  # Your project's URL
    packages=find_packages(),
    install_requires=[],  # Add any dependencies here
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)