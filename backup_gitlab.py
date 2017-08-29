#!/usr/bin/env python3

import os
import requests
import shutil
import subprocess
import sys
import time

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


def mirror_git_repo(http_url, repo_dir):
    try:
        run(['git', 'clone', '--mirror', http_url])
    except KeyboardInterrupt:
        clean(repo_dir)
        sys.exit(1)
    except Exception:
        clean(repo_dir)


def update_git_repo(repo_dir):
    try:
        old_dir = os.getcwd()
        os.chdir(repo_dir)
        run(['git', 'remote', 'update'])
    finally:
        os.chdir(old_dir)


def backup_gitlab():
    start = time.time()
    for project in get_projects():
        print('*'*80)
        web_url = project['web_url']
        print(web_url)

        http_url = project['ssh_url_to_repo']
        # Remove the entire url except the last part which is
        # what the mirrored directory will be called
        repo_dir = http_url.split('/')[-1]

        if os.path.isdir(repo_dir):
            try:
                update_git_repo(repo_dir)
            except subprocess.CalledProcessError:
                print('Updating repo_dir failed trying to delete and mirror')
                shutil.rmtree(repo_dir)
                mirror_git_repo(http_url, repo_dir)

        else:
            mirror_git_repo(http_url, repo_dir)
    end = time.time()
    print('took: ', end-start, 's')


def main():
    backup_gitlab()

if __name__ == '__main__':
    main()
