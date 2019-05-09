from setuptools import setup

setup(name='bispy',
      version='0.0.1',
      description='Essential logic for the Biogeographic Information System',
      url='http://github.com/usgs-bcb/bispy',
      author='R. Sky Bristol',
      author_email='bcb@usgs.gov',
      license='unlicense',
      packages=['bispy'],
      install_requires=[
            'requests',
            'boto3',
            'elasticsearch',
            'xmltodict'
      ],
      zip_safe=False)
