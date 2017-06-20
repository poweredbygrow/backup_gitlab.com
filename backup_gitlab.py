#!/usr/bin/env python3

import os
import requests
import shutil
import subprocess
import sys

import conf

params = {'private_token': conf.private_token,
          'membership': 'yes',
          'per_page': 100}
r = requests.get('https://gitlab.com/api/v4/projects', params=params)
obj = r.json()

os.makedirs(conf.backup_dir, exist_ok=True)
os.chdir(conf.backup_dir)


def clean(dir_to_clean):
    if os.path.isdir(dir_to_clean):
        shutil.rmtree(dir_to_clean)


for project in obj:
    print('*'*80)
    print(project['web_url'])
    http_url = project['ssh_url_to_repo']
    repo_dir = http_url.split('/')[-1]
    if os.path.isdir(repo_dir):
        try:
            old_dir = os.getcwd()
            os.chdir(repo_dir)
            cmd = ['git', 'remote', 'update']
            print("running", ' '.join(cmd))
            subprocess.check_call(cmd)
        finally:
            os.chdir(old_dir)
    else:
        try:
            cmd = ['git', 'clone', '--mirror', http_url]
            print("running", ' '.join(cmd))
            subprocess.check_call(cmd)
        except KeyboardInterrupt:
            clean(repo_dir)
            sys.exit(1)
        except:
            clean(repo_dir)
