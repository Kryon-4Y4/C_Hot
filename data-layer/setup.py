"""
data-layer: 共享数据层组件
为 phone-parts-trade-system 提供统一的数据库访问
"""
from setuptools import setup, find_packages

setup(
    name="data-layer",
    version="1.0.0",
    description="共享数据库访问层",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy==2.0.25",
        "psycopg2-binary==2.9.9",
        "pydantic==2.5.3",
    ],
    python_requires=">=3.9",
)
