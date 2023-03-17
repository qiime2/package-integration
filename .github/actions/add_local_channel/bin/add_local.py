import os
import subprocess

def _runcmd(cmd, verbose = False, *args, **kwargs):

    process = subprocess.Popen(
        cmd,
        stdout = subprocess.PIPE, 
        stderr = subprocess.PIPE,
        text = True, 
        shell = True
    )
    std_out, std_err = process.communicate()
    if verbose:
        print(std_out.strip(), std_err)
    pass

# epoch and platform need to be passed from enclosing action using the `with` syntax, should be found in inputs.epoch + inputs.platform
def fire_up_local_repo(epoch, platform, local_channel_name='local'):
    # get the files from the remote repo
    REMOTE_URL_PARENT = f'https://packages.qiime2.org/qiime2/'
    PATH_SUFFIX = f'{ epoch }/tested/{ platform }'
    FULL_REMOTE_URL = REMOTE_URL_PARENT + PATH_SUFFIX

    
    local_channel_path_root = os.path.join(os.getcwd(), local_channel_name)
    local_channel_path = os.path.join(local_channel_path_root, "packages.qiime2.org", PATH_SUFFIX)
  
  
    os.makedirs(local_channel_path_root, exist_ok=True)
    
    wget_call = f"wget --recursive -k --no-parent --cut-dirs=1 --level=inf --directory-prefix={local_channel_path} {FULL_REMOTE_URL}"

    _runcmd(wget_call, verbose=True)

    # setup and organize the conda channel
    

    _runcmd(f'conda config --add channels file://{local_channel_path}')
    _runcmd('conda config --show', verbose=True)
