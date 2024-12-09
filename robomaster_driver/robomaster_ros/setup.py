from setuptools import setup
import glob

package_name = 'robomaster_ros'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob.glob('launch/*.launch')),
        ('share/' + package_name + '/launch', glob.glob('launch/*.launch.py')),
        ('share/' + package_name + '/config', glob.glob('config/*'))
    ],
    install_requires=['setuptools', 'numpy', 'numpy-quaternion', 'pyyaml', 'robomaster'],
    zip_safe=True,
    maintainer='weiheng zhong',
    maintainer_email='weiheng_z@bit.edu.cn',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'teleoperation = robomaster_ros.teleoperation:main',
            'data_collection = robomaster_ros.data_collection:main',
        ],
    },
)
