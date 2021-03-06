from .undetected_chromedriver import install
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
import chromedriver_autoinstaller
import robot.settings as settings
import time
from selenium.webdriver.common.keys import Keys
import os
import sys
import os
import subprocess
import urllib.request
import urllib.error
import zipfile
import xml.etree.ElementTree as elemTree
import logging
import re

from io import BytesIO


class ChromeBrowser(Chrome):
    '''
    If chrome driver path is None, then it will check for Chrome Driver path in settings.
    Set undetectable True as flag to make chrome browser undetectable for antispam systems.
    '''

    def __init__(self, pathDriver=None, undetectable=False):
        self.CurrentPath = os.path.dirname(__file__)
        if not pathDriver:
            self.driver = install(settings.CHROMEDRIVER_PATH)
        else:
            self.driver = pathDriver
        self.options = Options()
        self.undetectable = undetectable

    def open(self):
        '''
        This method opens Chrome browser to start the navigation.
        Set Custom options before using this method.
        '''
        if self.undetectable:
            install(self.driver)
            from selenium.webdriver import Chrome
            from selenium.webdriver.chrome.options import Options
        else:
            pass
        super().__init__(self.driver, options=self.options)

    def ignoreImages(self):
        """Disable images in browser for a better performane"""

        prefs = {"profile.managed_default_content_settings.images": 2}
        self.options.add_experimental_option("prefs", prefs)

    def headless(self):
        """Hide Browser"""

        self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument("--headless")

    def saveCookies(self):
        """Save sesion cookies"""

        self.options.add_argument("--user-data-dir=selenium")

    def setProxy(self, proxy):
        """Use custom proxy"""

        self.options.add_argument('--proxy-server=http://%s' % proxy)

    def setUserAgent(self, userAgent):
        """Change default user agent"""

        self.options.add_argument("user-agent=" + userAgent)

    def setprofile(self, path):
        """Use syste chrome profile
        *Use this option if you are going to work with chrome plugins for example"""

        self.options.add_argument("user-data-dir=" + path)  # Path to your chrome profile

    def scrolldown(self, h=100):
        """Scroll down to % of the current page"""

        h = int(h)
        to_height = self.execute_script("return document.body.scrollHeight")
        to_height = (to_height * h) / 100
        actual_height = self.execute_script("return document.documentElement.scrollTop")
        for i in range(actual_height, to_height, 100):
            self.execute_script(f'window.scrollTo(0,{str(i)})')
            time.sleep(0.1)


def get_chromedriver_filename():
    """
    Returns the filename of the binary for the current platform.
    :return: Binary filename
    """
    if sys.platform.startswith('win'):
        return 'chromedriver.exe'
    return 'chromedriver'


def get_variable_separator():
    """
    Returns the environment variable separator for the current platform.
    :return: Environment variable separator
    """
    if sys.platform.startswith('win'):
        return ';'
    return ':'


def get_platform_architecture():
    if sys.platform.startswith('linux') and sys.maxsize > 2 ** 32:
        platform = 'linux'
        architecture = '64'
    elif sys.platform == 'darwin':
        platform = 'mac'
        architecture = '64'
    elif sys.platform.startswith('win'):
        platform = 'win'
        architecture = '32'
    else:
        raise RuntimeError('Could not determine chromedriver download URL for this platform.')
    return platform, architecture


def get_chromedriver_url(version):
    """
    Generates the download URL for current platform , architecture and the given version.
    Supports Linux, MacOS and Windows.
    :param version: chromedriver version string
    :return: Download URL for chromedriver
    """
    base_url = 'https://chromedriver.storage.googleapis.com/'
    platform, architecture = get_platform_architecture()
    return base_url + version + '/chromedriver_' + platform + architecture + '.zip'


def find_binary_in_path(filename):
    """
    Searches for a binary named `filename` in the current PATH. If an executable is found, its absolute path is returned
    else None.
    :param filename: Filename of the binary
    :return: Absolute path or None
    """
    if 'PATH' not in os.environ:
        return None
    for directory in os.environ['PATH'].split(get_variable_separator()):
        binary = os.path.abspath(os.path.join(directory, filename))
        if os.path.isfile(binary) and os.access(binary, os.X_OK):
            return binary
    return None


def check_version(binary, required_version):
    try:
        version = subprocess.check_output([binary, '-v'])
        version = re.match(r'.*?([\d.]+).*?', version.decode('utf-8'))[1]
        if version == required_version:
            return True
    except Exception:
        return False
    return False


def get_chrome_version():
    """
    :return: the version of chrome installed on client
    """
    platform, _ = get_platform_architecture()
    if platform == 'linux':
        executable_name = 'google-chrome'
        if os.path.isfile('/usr/bin/chromium-browser'):
            executable_name = 'chromium-browser'
        if os.path.isfile('/usr/bin/chromium'):
            executable_name = 'chromium'
        with subprocess.Popen([executable_name, '--version'], stdout=subprocess.PIPE) as proc:
            version = proc.stdout.read().decode('utf-8').replace('Chromium', '').replace('Google Chrome', '').strip()
    elif platform == 'mac':
        process = subprocess.Popen(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                                   stdout=subprocess.PIPE)
        version = process.communicate()[0].decode('UTF-8').replace('Google Chrome', '').strip()
    elif platform == 'win':
        process = subprocess.Popen(
            ['reg', 'query', 'HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon', '/v', 'version'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
        )
        version = process.communicate()[0].decode('UTF-8').strip().split()[-1]
    else:
        return
    return version


def get_major_version(version):
    """
    :param version: the version of chrome
    :return: the major version of chrome
    """
    return version.split('.')[0]


def get_matched_chromedriver_version(version):
    """
    :param version: the version of chrome
    :return: the version of chromedriver
    """
    doc = urllib.request.urlopen('https://chromedriver.storage.googleapis.com').read()
    root = elemTree.fromstring(doc)
    for k in root.iter('{http://doc.s3.amazonaws.com/2006-03-01}Key'):
        if k.text.find(get_major_version(version) + '.') == 0:
            return k.text.split('/')[0]
    return


def get_chromedriver_path():
    """
    :return: path of the chromedriver binary
    """
    return os.path.abspath(os.path.dirname(__file__))


def print_chromedriver_path():
    """
    Print the path of the chromedriver binary.
    """
    print(get_chromedriver_path())


def download_chromedriver(cwd=None):
    """
    Downloads, unzips and installs chromedriver.
    If a chromedriver binary is found in PATH it will be copied, otherwise downloaded.

    :param cwd: Flag indicating whether to download to current working directory
    :return: The file path of chromedriver
    """
    chrome_version = get_chrome_version()
    if not chrome_version:
        logging.debug('Chrome is not installed.')
        return
    chromedriver_version = get_matched_chromedriver_version(chrome_version)
    if not chromedriver_version:
        logging.debug('Can not find chromedriver for currently installed chrome version.')
        return
    major_version = get_major_version(chromedriver_version)

    if cwd:
        chromedriver_dir = cwd
    else:
        chromedriver_dir = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            major_version
        )
    chromedriver_filename = get_chromedriver_filename()
    chromedriver_filepath = os.path.join(chromedriver_dir, chromedriver_filename)
    if not os.path.isfile(chromedriver_filepath) or \
            not check_version(chromedriver_filepath, chromedriver_version):
        logging.debug(f'Downloading chromedriver ({chromedriver_version})...')
        if not os.path.isdir(chromedriver_dir):
            os.mkdir(chromedriver_dir)
        url = get_chromedriver_url(version=chromedriver_version)
        try:
            response = urllib.request.urlopen(url)
            if response.getcode() != 200:
                raise urllib.error.URLError('Not Found')
        except urllib.error.URLError:
            raise RuntimeError(f'Failed to download chromedriver archive: {url}')
        archive = BytesIO(response.read())
        with zipfile.ZipFile(archive) as zip_file:
            zip_file.extract(chromedriver_filename, chromedriver_dir)
    else:
        logging.debug('Chromedriver is already installed.')
    if not os.access(chromedriver_filepath, os.X_OK):
        os.chmod(chromedriver_filepath, 0o744)
    return chromedriver_filepath


def install(cwd=None):
    """
    Appends the directory of the chromedriver binary file to PATH.

    :param cwd: Flag indicating whether to download to current working directory
    :return: The file path of chromedriver
    """
    directory = cwd
    chromedriver_filepath = download_chromedriver(directory)
    if not chromedriver_filepath:
        logging.debug('Can not download chromedriver.')
        return
    chromedriver_dir = os.path.dirname(chromedriver_filepath)
    if 'PATH' not in os.environ:
        os.environ['PATH'] = chromedriver_dir
    elif chromedriver_dir not in os.environ['PATH']:
        os.environ['PATH'] = chromedriver_dir + get_variable_separator() + os.environ['PATH']
    return chromedriver_filepath
