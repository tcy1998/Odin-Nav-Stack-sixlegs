from setuptools import setup
import os
from glob import glob

package_name = 'neupan_ros2'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include launch files
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        # Include config files
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='tcy1998',
    maintainer_email='tcy1998@example.com',
    description='ROS2 implementation of NeuPAN for Dobot Mini Hex V2',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'neupan_node = neupan_ros2.neupan_node:main',
            'dune_node = neupan_ros2.dune_node:main',
        ],
    },
)
