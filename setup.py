try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requires = ['asyncio', 'aiohttp', 'bottle']

setup(
    name='aiobottle',
    version='0.1.1',
    description='Aiobottle, a warper bottle use aiohttp base on  Asyncio (PEP-3156)',
    author='Li Meng Jun',
    author_email='lmjubuntu@gmail.com',
    url='https://github.com/Lupino/aiobottle',
    py_modules=['aiobottle'],
    include_package_data=True,
    install_requires=requires,
)
