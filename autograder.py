import subprocess
import csv
import os
import shutil
from collections import defaultdict

import requests
import argparse

organization = "uva-cs4740"
wc = "test-mr-wc.sh"
indexer = "test-mr-indexer.sh"
map_parallelism = "test-mr-mtiming.sh"
reduce_parallelism = "test-mr-rtiming.sh"
job_count = "test-mr-jobcount.sh"
early_exit = "test-mr-early-exit.sh"
crash = "test-mr-crash.sh"
student_name_computing_id_map={}

test_weight = {
            wc: 5,
            indexer: 5,
            map_parallelism: 3,
            reduce_parallelism: 3,
            job_count: 2,
            early_exit: 1,
            crash: 1,
        }


def run_command(command):
    try:
        subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print(f"Error executing {command}: {e.output}")
        raise


def clone_repos(repo_list, workspace_dir):
    create_dir_cmd = f"mkdir -p {workspace_dir}"
    run_command(create_dir_cmd)

    for repo_url in repo_list:
        repo_name = repo_url.split('/')[-1].strip()
        clone_cmd = f"cd {workspace_dir} && git clone https://github.com/uva-cs4740/{repo_name}"
        run_command(clone_cmd)


def checkout_branch(workspace_dir, branch_name):
    error_list ={}
    for repo_dir in os.listdir(workspace_dir):
        repo_path = os.path.join(workspace_dir, repo_dir)
        if os.path.isdir(repo_path):
            checkout_cmd = f"cd {repo_path} && git checkout {branch_name}"
            try:
                subprocess.check_output(checkout_cmd, shell=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                error_list[repo_dir]=0
    return error_list



def replace_test_codes(workspace_dir, original_tests_dir):
    for repo_dir in os.listdir(workspace_dir):
        repo_path = os.path.join(workspace_dir, repo_dir)
        tests_path = os.path.join(repo_path, 'src/main')
        mrapps_path = os.path.join(repo_path, 'src/mrapps')
        if os.path.isdir(tests_path):
            # delete existing test scripts
            test_scripts = ['test-mr-crash.sh', 'test-mr-early-exit.sh','test-mr-indexer.sh','test-mr-jobcount.sh','test-mr-mtiming.sh',
                            'test-mr-rtiming.sh','test-mr-wc.sh','test-mr-many.sh']
            for script in test_scripts:
                script_path = os.path.join(tests_path, script)
                if os.path.exists(script_path):
                    os.remove(script_path)

            # replace with original test scripts
            for script in test_scripts:
                original_script_path = os.path.join(original_tests_dir, script)
                if os.path.exists(original_script_path):
                    shutil.copy(original_script_path, tests_path)
                else:
                    shutil.copy2(original_script_path, tests_path)
        if os.path.exists(mrapps_path):
            shutil.rmtree(mrapps_path)

        os.makedirs(mrapps_path)
        test_mrapp = original_tests_dir + "/mrapps"

        for item in os.listdir(test_mrapp):
            src_path = os.path.join(test_mrapp, item)
            dst_path = os.path.join(mrapps_path, item)
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dst_path)
            else:
                shutil.copy2(src_path, dst_path)



def run_command_and_parse(test_cmd, dict, key):
    print("run_command_and_parse")
    try:
        output_content = subprocess.check_output(test_cmd, shell=True, env=os.environ)
        dict[key] = 1
        print(test_cmd+"pass")
    except subprocess.CalledProcessError as e:
        dict[key] = 0


def get_student_name(repo_dir):
    #the student_info file is in repo_path, and the format is student_name, student_id, create a map of {repo_path:student_name}
    repo_path = os.path.join(workspace_dir, repo_dir)

    student_info_file = "student_info"
    student_info_path= os.path.join(repo_path, student_info_file)
    #if student_info file does not exist, set student_name_computing_id_map[repo_dir] to be repo_dir
    if not os.path.exists(student_info_path):
        student_name_computing_id_map[repo_dir] = repo_dir
        print("does not exist student_info_file")
        return
    with open(student_info_path, 'r') as file:
        try:
            student_info = file.readlines()
            student_name = student_info[0].strip() if student_info else repo_dir
            student_name_computing_id_map[repo_dir] = student_name
            print(student_name)
        except Exception as e:
            print(f"Error reading file: {e}")
            student_name_computing_id_map[repo_dir] = repo_dir


def run_tests(workspace_dir, num_trials,error_list):
    #results should be a map of {repo_dir: {test_name: pass/fail}}
    results = {}
    go_set_env_command = "go env -w GO111MODULE=on"
    list = [wc, indexer, map_parallelism, reduce_parallelism, job_count, early_exit, crash]
    subprocess.check_output(go_set_env_command, shell=True, env=os.environ)
    for repo_dir in os.listdir(workspace_dir):
        get_student_name(repo_dir)
        results[repo_dir] = {}
        if repo_dir in error_list.keys():
            for test in list:
                results[repo_dir][test] = 0
            continue
        test_pass_count = {
            wc: 0,
            indexer: 0,
            map_parallelism: 0,
            reduce_parallelism: 0,
            job_count: 0,
            early_exit: 0,
            crash: 0,
        }

        repo_path = os.path.join(workspace_dir, repo_dir)
        try:
            commit_count = int(subprocess.check_output(f"git rev-list --count HEAD", shell=True, cwd=repo_path).strip())
        except subprocess.CalledProcessError:
            commit_count = 0
        if commit_count <=1 :
            for test in list:
                results[repo_dir][test] = 0
            continue

        test_cmd_wc = f"cd {repo_path}/src/main && bash test-mr-many.sh {num_trials} {wc}"
        test_cmd_indexer = f"cd {repo_path}/src/main && bash test-mr-many.sh {num_trials} {indexer}"
        test_cmd_crash = f"cd {repo_path}/src/main && bash test-mr-many.sh {num_trials} {crash}"
        test_cmd_early_exit = f"cd {repo_path}/src/main && bash test-mr-many.sh {num_trials} {early_exit}"
        test_cmd_mtiming = f"cd {repo_path}/src/main && bash test-mr-many.sh {num_trials} {map_parallelism}"
        test_cmd_rtiming = f"cd {repo_path}/src/main && bash test-mr-many.sh {num_trials} {reduce_parallelism}"
        test_cmd_jobcount = f"cd {repo_path}/src/main && bash test-mr-many.sh {num_trials} {job_count}"
        run_command_and_parse(test_cmd_wc, test_pass_count,wc)
        run_command_and_parse(test_cmd_indexer, test_pass_count,indexer)
        run_command_and_parse(test_cmd_crash, test_pass_count,crash)
        run_command_and_parse(test_cmd_early_exit, test_pass_count,early_exit)
        run_command_and_parse(test_cmd_mtiming, test_pass_count,map_parallelism)
        run_command_and_parse(test_cmd_rtiming, test_pass_count,reduce_parallelism)
        run_command_and_parse(test_cmd_jobcount, test_pass_count,job_count)
        for test in list:
            results[repo_dir][test]=test_pass_count[test]
    return results


def write_to_csv(results, output_file):
    #the column in csv file should be student_name, wc, indexer, map_parallelism, reduce_parallelism, job_count, early_exit, crash
    with open(output_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["student_name", "wc", "indexer", "map_parallelism", "reduce_parallelism", "job_count", "early_exit", "crash"])
        for repo_name, result in results.items():
            writer.writerow([student_name_computing_id_map[repo_name], result[wc], result[indexer], result[map_parallelism], result[reduce_parallelism], result[job_count], result[early_exit], result[crash]])


def main(repo_path, workspace_dir, original_tests_dir, branch_name, output_file, num_trails, token, single_student_url):
    if single_student_url != None:
        repo_list = [single_student_url]
    else:
        get_repo_list(repo_path, token)
        with open(repo_path) as f:
            repo_list = [line.strip() for line in f.readlines()]
            repo_list = repo_list[0:10]

    clone_repos(repo_list, workspace_dir)
    error_list = checkout_branch(workspace_dir, branch_name)
    replace_test_codes(workspace_dir, original_tests_dir)
    results = run_tests(workspace_dir, num_trails, error_list)
    write_to_csv(results, output_file)


def get_repo_list(repo_list_path, token):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
    }

    # Initialize the URL for the first page of the repository list
    url = f'https://api.github.com/orgs/{organization}/repos'

    # List to store all repository clone URLs
    repo_list = []

    while url:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            repos = response.json()
            for repo in repos:
                repo_list.append(repo['clone_url'])
                print(repo['clone_url'])

            # GitHub API includes pagination links in response headers
            # Check if there's a 'next' page and update the URL, or break the loop if we're on the last page
            if 'next' in response.links:
                url = response.links['next']['url']
            else:
                break  # Exit loop if there are no more pages
        else:
            print('Request failed with status code:', response.status_code)
            break  # Exit loop if there's an error

    with open(repo_list_path, 'w') as file:
        for repo in repo_list:
            file.write(repo + '\n')


def get_go_bin_path():
    try:
        goroot = subprocess.check_output(["go", "env", "GOROOT"], text=True).strip()
        go_bin_path = os.path.join(goroot, "bin")
        return go_bin_path
    except subprocess.CalledProcessError:
        print("Go is not installed")
        return None


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--github_token", required=False, default="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",
                        help="personal github token to get the repo list in Github Classroom")
    parser.add_argument("--repo_path", required=False, default="repo_list.txt",
                        help="the list for the students' repo url")
    parser.add_argument("--workspace", required=False, default="workspace",
                        help="the dir to store students' repo")
    parser.add_argument("--original_tests_dir", required=False, default="lab1",
                        help="the original test file")
    parser.add_argument("--branch_name", required=False, default="lab1",
                        help="the branch to check out")
    parser.add_argument("--output_file", required=False, default="output.csv",
                        help="the file to store students' grade")
    parser.add_argument("--num_trails", required=False, default=1, help="the number to repeat the test")
    parser.add_argument("--single_student_url", required=False, help="the url of a single student")
    args = parser.parse_args()
    github_token = args.github_token
    repo_path = args.repo_path
    original_tests_dir = "tests/" + args.original_tests_dir
    workspace_dir = args.workspace
    branch_name = args.branch_name
    output_file = args.output_file
    num_trails = args.num_trails
    current_path = os.environ.get("PATH", "")
    new_path = get_go_bin_path() + os.pathsep + current_path
    os.environ["PATH"] = new_path

    if os.path.exists(workspace_dir):
        shutil.rmtree(workspace_dir)

    if os.path.exists(output_file):
        os.remove(output_file)

    main(repo_path, workspace_dir, original_tests_dir, branch_name, output_file, num_trails, github_token,
         args.single_student_url)
