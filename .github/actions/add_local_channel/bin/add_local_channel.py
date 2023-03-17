import os
import requests
import urllib.request

def download_and_setup_conda_channel(remote_url, local_repo_name='qiime8-local'):
    # Define the URL of the file server directory
    remote_url = remote_url
    
    # Define the name of the local conda channel to create
    conda_channel_name = local_repo_name
    
    # Define the path where the local conda channel will be created
    conda_channel_path = os.path.join(os.getcwd(), conda_channel_name)
    
    # Create the local conda channel directory
    os.makedirs(conda_channel_path, exist_ok=True)

    # Send a GET request to the website URL
    response = requests.get(remote_url)

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract all links from the HTML content
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and not href.startswith('#'):
            links.append(href)

    # Download all files from the current URL
    for link in links:
        file_url = urljoin(url, link)
        if file_url.endswith('/'):
            # If the link is a directory, recursively download all files from it
            download_files(file_url)
        else:
            # If the link is a file, download it to the local directory
            file_name = os.path.basename(urlparse(file_url).path)
            local_path = os.path.join(conda_channel_path, file_name)

            # Send a GET request to the file URL
            response = requests.get(file_url)

            # Save the file to the local directory
            with open(local_path, 'wb') as f:
                f.write(response.content)

            print(f'Downloaded {file_name} from {url}')


    ########### working edge
    # Parse the response content and extract all links
    links = []
    for line in response.content.decode().splitlines():
        if 'href="' in line:
            link = line.split('href="')[1].split('"')[0]
            links.append(link)
    # Download all files from the website
    for link in links:
        file_url = f'{remote_url}/{link}'
        file_name = os.path.basename(urlparse(file_url).path)
        local_path = os.path.join(local_directory, file_name)
    
        # Send a GET request to the file URL
        response = requests.get(file_url)
    
        # Save the file to the local directory
        with open(local_path, 'wb') as f:
            f.write(response.content)

        print(f'Downloaded {file_name}')




    # Download the files from the file server directory
    urllib.request.urlretrieve(f'{remote_url}/package1.tar.bz2',
                               os.path.join(os.getcwd(), 'package1.tar.bz2'))
    urllib.request.urlretrieve(f'{remote_url}/package2.tar.bz2',
                               os.path.join(os.getcwd(), 'package2.tar.bz2'))
    
    
    # Extract the downloaded files to the local conda channel directory
    shutil.unpack_archive(os.path.join(os.getcwd(), 'package1.tar.bz2'), os.path.join(conda_channel_path, 'pkgs'))
    shutil.unpack_archive(os.path.join(os.getcwd(), 'package2.tar.bz2'), os.path.join(conda_channel_path, 'pkgs'))
    
    # Add the local conda channel to conda's configuration
    os.system(f'conda config --add channels file://{conda_channel_path}')
    
import os
import requests
from urllib.parse import urlparse


# Define the local directory to save the downloaded files to
local_directory = os.path.join(os.getcwd(), 'downloaded_files')

# Create the local directory if it doesn't exist
os.makedirs(local_directory, exist_ok=True)

# Send a GET request to the website URL
response = requests.get(website_url)

# Parse the response content and extract all links
links = []
for line in response.content.decode().splitlines():
    if 'href="' in line:
        link = line.split('href="')[1].split('"')[0]
        links.append(link)

# Download all files from the website
for link in links:
    file_url = f'{website_url}/{link}'
    file_name = os.path.basename(urlparse(file_url).path)
    local_path = os.path.join(local_directory, file_name)

    # Send a GET request to the file URL
    response = requests.get(file_url)

    # Save the file to the local directory
    with open(local_path, 'wb') as f:
        f.write(response.content)

    print(f'Downloaded {file_name}')

import os
import requests
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

# Define the URL of the website to download files from
website_url = 'http://example.com/'

# Define the local directory to save the downloaded files to
local_directory = os.path.join(os.getcwd(), 'downloaded_files')

# Create the local directory if it doesn't exist
os.makedirs(local_directory, exist_ok=True)

def download_files(url):
    # Send a GET request to the URL
    response = requests.get(url)

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract all links from the HTML content
    links = []
    for link in soup.find_all('a'):
        href = link.get('href')
        if href and not href.startswith('#'):
            links.append(href)

    # Download all files from the current URL
    for link in links:
        file_url = urljoin(url, link)
        if file_url.endswith('/'):
            # If the link is a directory, recursively download all files from it
            download_files(file_url)
        else:
            # If the link is a file, download it to the local directory
            file_name = os.path.basename(urlparse(file_url).path)
            local_path = os.path.join(local_directory, file_name)

            # Send a GET request to the file URL
            response = requests.get(file_url)

            # Save the file to the local directory
            with open(local_path, 'wb') as f:
                f.write(response.content)

            print(f'Downloaded {file_name} from {url}')

# Download all files from the website recursively
download_files(website_url)

