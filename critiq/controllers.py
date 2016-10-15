import json
import subprocess

import os
import requests
from git import Repo
from unidiff import PatchSet

pwd = os.path.abspath(os.path.dirname(__file__))
repo = Repo(os.path.abspath(pwd))

PERSONAL_ACCESS_TOKEN = "<GitLab Access Token>"  # TODO: Replace with GitLab Access token
GITLAB_ME = "<GitLab user name>"  # TODO: Replace with gitlab username
REPO_NAME = "<GitLab Repo name>"  # TODO: repo name, e.g. "opinew/product_reviews"


def cache(function):
    def wrapper():
        try:
            with open("cache/%s" % function.__name__) as f:
                response = f.read()
                return json.loads(response)
        except Exception as e:
            print e.message
        response = function()
        with open("cache/%s" % function.__name__, 'w') as f:
            f.write(json.dumps(response))

        return response

    return wrapper


@cache
def list_remote_branches():
    response = requests.get(
        "https://gitlab.com/api/v3/projects/{repo_name}/repository/branches".format(repo_name=REPO_NAME),
        headers={
            "PRIVATE-TOKEN": PERSONAL_ACCESS_TOKEN,
        })
    response = response.json()
    return response


@cache
def list_own_issues():
    response = requests.get(
        "https://gitlab.com/api/v3/projects/{repo_name}/issues".format(repo_name=REPO_NAME),
        data={
            "state": "opened",
        },
        headers={
            "PRIVATE-TOKEN": PERSONAL_ACCESS_TOKEN,
        })
    response = response.json()
    rv = []
    for r in response:
        if r['assignee'] and r['assignee']['username'] and r['assignee']['username'] == GITLAB_ME:
            rv.append(r)
    return rv


def list_problems():
    if not os.path.isfile("cache/prospector.json"):
        os.system("prospector")
    with open("cache/prospector.json") as f:
        response = f.read()
        return json.loads(response)


def coverage_report():
    if not os.path.isfile("cache/coverage.txt"):
        os.system("coverage run tests.py")
    with open("cache/coverage.txt") as f:
        response = f.read()
        return response


def git_diff(patches):
    added_files = len(patches.added_files) if hasattr(patches, 'added_files') else 0
    modified_files = len(patches.modified_files) if hasattr(patches, 'modified_files') else 0
    removed_files = len(patches.removed_files) if hasattr(patches, 'removed_files') else 0
    diffs = {
        'summary': {
            'added_files': added_files,
            'modified_files': modified_files,
            'removed_files': removed_files,
            'added_lines': 0,
            'removed_lines': 0
        },
        'files': []
    }
    for patch in patches:
        diffs['summary']['added_lines'] += patch.added
        diffs['summary']['removed_lines'] += patch.removed
        added, removed = [], []
        for hunk in patch:
            for line in hunk:
                if line.is_added:
                    added.append(line.target_line_no)
                elif line.is_removed:
                    removed.append(line.source_line_no)
        diffs['files'].append({'path': patch.path, 'added': added, 'removed': removed})
    return diffs


def diff_with_index():
    t = repo.head.commit.tree
    diff = repo.git.diff(t)
    patches = PatchSet(diff.split('\n'))
    return git_diff(patches)


def diff_with_prev_commit():
    commits_list = list(repo.iter_commits())
    if not len(commits_list) > 1:
        return git_diff([])
    b_commit = commits_list[1]
    diff = repo.git.diff(b_commit)
    patches = PatchSet(diff.split('\n'))
    return git_diff(patches)


def diff_with_branch():
    diff = repo.git.diff(repo.branches.master.commit)
    patches = PatchSet(diff.split('\n'))
    return git_diff(patches)


def list_problems_new(problems, changed_files):
    changed_files_dict = {cf['path']: {'added': cf['added']} for cf in changed_files}
    new_problems = {'messages': []}
    for problem in problems['messages']:
        if problem['location']['path'] in changed_files_dict and \
                        problem['location']['line'] in changed_files_dict.get(problem['location']['path'], {}).get(
                    'added'):
            new_problems['messages'].append(problem)
    return new_problems


def list_coverage_new(coverage, changed_files):
    changed_files_dict = {cf['path'].replace('/', '_'): {'added': cf['added']} for cf in changed_files}
    new_coverage_misses = {
        'summary': {
            'total_misses': 0
        },
        'files': []
    }
    for file_status in coverage['files']:
        file_name = file_status['path']
        new_missed_lines = []
        for missed_line in file_status['misses']:
            if file_name in changed_files_dict and missed_line in changed_files_dict.get(file_name, {}).get('added'):
                new_missed_lines.append(missed_line)
        new_coverage_misses['files'].append({
            'path': file_status['path'],
            'lines': file_status['lines'],
            'misses': new_missed_lines,
            'content': file_status['content']
        })
        new_coverage_misses['summary']['total_misses'] += len(new_missed_lines)
    return new_coverage_misses


def get_coverage():
    coverage = {
        'summary': {
            'total_misses': 0
        },
        'files': []
    }
    for filename in os.listdir("cache/cover"):
        reported_filename = filename.split(',')[0]
        with open("cache/cover/%s" % filename) as f:
            content = f.readlines()
            line_statuses = []
            line_misses = []
            for lineno, line in enumerate(content):
                line_status = "unknown"
                if len(line):
                    if line[0] == '>':
                        line_status = "covered"
                    elif line[0] == '-':
                        line_status = "excluded"
                    elif line[0] == '!':
                        line_status = "missed"
                        line_misses.append(lineno + 1)
                line_statuses.append(line_status)
        coverage['files'].append({
            'path': reported_filename,
            'lines': line_statuses,
            'misses': line_misses,
            'content': [a[2:-1] for a in content]
        })
        coverage['summary']['total_misses'] += len(line_statuses)
    return coverage


def repo_reattach_head():
    command = "git name-rev --name-only HEAD"
    proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()
    branch = out.split('/')[-1]
    os.system("git checkout %s" % branch)
    os.system("git pull")
    os.system("git checkout master")
    os.system("git pull origin master")
    os.system("git checkout %s" % branch)


def report(no_own_issues=False, no_remote_branches=False):
    ctx = dict()
    if not no_own_issues:
        ctx['own_issues'] = list_own_issues()

    if not repo.head.is_detached:
        ctx['current_branch'] = repo.active_branch.name
        ctx['local_branches'] = [b.name for b in repo.branches]

    if not no_remote_branches:
        ctx['remote_branches'] = list_remote_branches()

    ctx['index_changes'] = diff_with_index()
    ctx['commit_changes'] = diff_with_prev_commit()
    ctx['branch_changes'] = diff_with_branch()

    ctx['coverage_report'] = coverage_report()
    ctx['coverage'] = get_coverage()
    ctx['coverage_new_index'] = list_coverage_new(ctx['coverage'], ctx['index_changes']['files'])
    ctx['coverage_new_commit'] = list_coverage_new(ctx['coverage'], ctx['commit_changes']['files'])
    ctx['coverage_new_branch'] = list_coverage_new(ctx['coverage'], ctx['branch_changes']['files'])

    ctx['problems'] = list_problems()
    ctx['problems_new_index'] = list_problems_new(ctx['problems'], ctx['index_changes']['files'])
    ctx['problems_new_commit'] = list_problems_new(ctx['problems'], ctx['commit_changes']['files'])
    ctx['problems_new_branch'] = list_problems_new(ctx['problems'], ctx['branch_changes']['files'])
    return ctx


def report_all(ctx):
    print
    print "Coverage"
    print "==============="
    print ctx.get("coverage_report")
    print
    print
    print "All Uncovered lines"
    print "=============="
    for coverage_status in ctx.get('coverage', {}).get('files', []):
        if coverage_status.get('misses', []):
            print "Missed in %s:" % (coverage_status.get('path', ''))
            for line_miss in coverage_status.get('misses', []):
                print "    %s: %s" % (line_miss, coverage_status.get('content')[line_miss - 1])
            print
    print "All problems"
    print "=============="
    for problem in ctx.get('problems', {}).get('messages', []):
        print "%s:%s - %s - %s" % (
            problem.get("location", {}).get("path", {}), problem.get("location").get("line"), problem.get("source"),
            problem.get('message'))
    print
    print


def report_pretty(all=False):
    if repo.head.is_detached:
        repo_reattach_head()
    ctx = report(no_own_issues=True, no_remote_branches=True)
    print
    print "** REPORT **"
    print "***********************"
    print
    print
    print "COVERAGE"
    print "Uncovered lines in commit"
    print "=============="
    for coverage_status in ctx.get('coverage_new_commit', {}).get('files', []):
        if coverage_status.get('misses', []):
            print "Missed in %s:" % (coverage_status.get('path', ''))
            for line_miss in coverage_status.get('misses', []):
                print "    %s: %s" % (line_miss, coverage_status.get('content')[line_miss - 1])
            print
    print
    print
    print "Uncovered lines in branch"
    print "=============="
    for coverage_status in ctx.get('coverage_new_branch', {}).get('files', []):
        if coverage_status.get('misses', []):
            print "Missed in %s:" % (coverage_status.get('path', ''))
            for line_miss in coverage_status.get('misses', []):
                print "    %s: %s" % (line_miss, coverage_status.get('content')[line_miss - 1])
            print
    print
    print
    print "PROBLEMS"
    print "New problems in commit"
    print "=============="
    for problem in ctx.get('problems_new_commit', {}).get('messages', []):
        print "%s:%s - %s - %s" % (
            problem.get("location", {}).get("path", {}), problem.get("location").get("line"), problem.get("source"),
            problem.get('message'))
    print
    print
    print "New problems in branch"
    print "=============="
    for problem in ctx.get('problems_new_branch', {}).get('messages', []):
        print "%s:%s - %s - %s" % (
            problem.get("location", {}).get("path", {}), problem.get("location").get("line"), problem.get("source"),
            problem.get('message'))
    print
    print
    if all:
        report_all(ctx)
