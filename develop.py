from distutils.core import setup

#from setup import NAME, MAJOR_VERSION, PACKAGES, \
#    INSTALL_REQUIRES, DEPENDENCY_LINKS, SCRIPTS, PACKAGE_DATA

setup(
    name="workbench",
    version="0.0",
    packages=["workbench"],
    #package_data=PACKAGE_DATA,
    #install_requires=INSTALL_REQUIRES + ["mock", "coverage", "Sphinx", "metrics"],
    #dependency_links=DEPENDENCY_LINKS,
    #scripts=SCRIPTS,
    test_suite="test.all",
)
