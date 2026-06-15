import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'doosan_printing_app'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name), glob('doosan_printing_app/*.txt')),
    ],
    install_requires=['setuptools', 'pyserial'],
    zip_safe=True,
    maintainer='sonnguyen',
    maintainer_email='sonnguyen@gmail.com',
    description='Dự án NCKH: Điều khiển robot Doosan A0509 ứng dụng in 3D 5 trục',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'doosan_printer = doosan_printing_app.doosan_printer_node:main',
            'doosan_printer_node = doosan_printing_app.doosan_printer_node:main',
            'smart_printer_5axis_pro = doosan_printing_app.doosan_printer_node:main',
        ],
    },
)