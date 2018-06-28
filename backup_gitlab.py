#!/usr/bin/env python3

import datetime
import logging
import os
import requests
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.realpath(__file__))

import conf

os.makedirs(os.path.join(ROOT, 'log'), exist_ok=True)
logging.basicConfig(filename=datetime.datetime.now().strftime(os.path.join(ROOT, "log/gitlabbackup_%Y_%m_%d_%H_%M.log")), level=logging.INFO)
logger = logging.getLogger('gitlab-backup')


def clean(dir_to_clean):
    if os.path.isdir(dir_to_clean):
        shutil.rmtree(dir_to_clean)


def run(cmd):
    logger.info("running:" + ' '.join(cmd))
    subprocess.check_call(cmd)


def get_projects():
    projects = []
    page = 1
    while True:
        params = {'private_token': conf.private_token,
                  'membership': 'yes',
                  'per_page': 50,
                  'page': page,
                  'order_by': 'name',
                  'sort': 'asc'}
        r = requests.get('https://gitlab.com/api/v4/projects', params=params)
        if r.status_code != 200:
            raise Exception("Didn't get a 200. Code: " + str(r.status_code) + "\nBody:\n" + r.text)
        new_projects = r.json()
        names = [project['name'] for project in new_projects]
        logger.info('Got: ' + ' '.join(names))
        if len(new_projects) == 0:
            break
        page += 1
        projects += new_projects

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
    os.makedirs(conf.backup_dir, exist_ok=True)
    os.chdir(conf.backup_dir)

    projects = get_projects()
    print('Found ', len(projects), 'projects')
    for project in projects:
        print('*'*80)
        id = project['id']
        web_url = project['web_url']
        print('id:', id, 'web_url:', web_url)

        http_url = project['ssh_url_to_repo']
        # Remove the entire url except the last part which is
        # what the mirrored directory will be called
        repo_dir = http_url.split('/')[-1]

        if os.path.isdir(repo_dir):
            try:
                update_git_repo(repo_dir)
            except subprocess.CalledProcessError:
                logger.info('Updating repo_dir failed. Trying to delete and mirror')
                shutil.rmtree(repo_dir)
                mirror_git_repo(http_url, repo_dir)

        else:
            mirror_git_repo(http_url, repo_dir)
    end = time.time()
    logger.info('took: ' + str(end-start) + 's')


def main():
    backup_gitlab()


if __name__ == '__main__':
    main()
