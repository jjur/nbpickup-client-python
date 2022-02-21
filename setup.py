import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nbpickup",
    version="0.9.0",
    author="Juraj Vasek",
    author_email="juraj.vasek@uni.minerva.edu",
    description="Library for collecting and distribution of coding assessments using nbgrader and Binder.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jjur/nbpickup-client-python",
    packages=setuptools.find_packages(),
    license='MIT',
    python_requires='>=3',
    install_requires=['requests', "ipykernel", "ipython", "watchdog", "nbgrader"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)