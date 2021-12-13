import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="nonebot_plugin_picsbank",
    version="0.1.1",
    author="Alex Newton",
    author_email="sharenfan222@gmail.com",
    description="a picture response plugin",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Diaosi1111/nonebot_plugin_picsbank",
    project_urls={
        "Bug Tracker": "https://github.com/Diaosi1111/nonebot_plugin_picsbank/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.8,<3.11",
)
