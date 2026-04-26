from setuptools import setup, find_packages

setup(
    name="autonomous-data-analyst",
    version="1.0.0",
    description="Agentic AI pipeline for autonomous data analysis",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=open("requirements.txt").read().splitlines(),
    entry_points={
        "console_scripts": [
            "analyst=cli:main",
        ],
    },
)
