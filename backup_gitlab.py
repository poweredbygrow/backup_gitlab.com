#!/usr/bin/env python3

import os
import requests
import shutil
import subprocess
import sys

import conf


def clean(dir_to_clean):
    if os.path.isdir(dir_to_clean):
        shutil.rmtree(dir_to_clean)


def run(cmd):
    print("running", ' '.join(cmd))
    subprocess.check_call(cmd)


def get_projects():
    params = {'private_token': conf.private_token,
              'membership': 'yes',
              'per_page': 100}
    r = requests.get('https://gitlab.com/api/v4/projects', params=params)
    projects = r.json()

    os.makedirs(conf.backup_dir, exist_ok=True)
    os.chdir(conf.backup_dir)
    return projects


def backup_gitlab():
    for project in get_projects():
        print('*'*80)
        print(project['web_url'])
        http_url = project['ssh_url_to_repo']
        repo_dir = http_url.split('/')[-1]
        if os.path.isdir(repo_dir):
            try:
                old_dir = os.getcwd()
                os.chdir(repo_dir)
                cmd = ['git', 'remote', 'update']
                run(cmd)
            finally:
                os.chdir(old_dir)
        else:
            try:
                cmd = ['git', 'clone', '--mirror', http_url]
                run(cmd)
            except KeyboardInterrupt:
                clean(repo_dir)
                sys.exit(1)
            except:
                clean(repo_dir)


def main():
    backup_gitlab()

if __name__ == '__main__':
    main()
