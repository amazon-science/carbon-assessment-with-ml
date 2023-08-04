import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='caml',
    version='1.0.0',
    author='Bharathan Balaji',
    author_email='bhabalaj@amazon.com',
    description='Carbon assessment with machine learning',
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=['caml'],
)
