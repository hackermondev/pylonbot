from setuptools import setup, find_packages

setup(
    name="pylon",
    version="1.0",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "sanic",
        "asyncpg==0.20.1",
        "oauthlib==3.1.0",
        "itsdangerous==1.1.0",
        "pyjwt==2.4.0",
        "pydantic==1.5.1",
        "simplejson==3.17.0",
        "sentry-sdk==0.14.3",
        "grpclib==0.3.1",
        "uvloop==0.14.0",
        # CLI Shell
        "ipython==7.13.0",
    ],
    setup_requires=["pytest-runner"],
    tests_require=["pytest==5.4.1", "pytest-asyncio"],
    scripts=["bin/hell"],
    dependency_links=["git+https://github.com/huge-success/sanic.git#egg=sanic"],
)
