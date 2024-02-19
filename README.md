# UVa CS4740 Automation Test Tool

This tool is designed to automate the process of cloning student repositories from GitHub Classroom, running tests against those repositories, and generating a grading report. It supports both batch processing of repositories listed in a file and processing a single repository specified by URL.



## Features

- Clone student repositories from GitHub Classroom using a personal GitHub token.
- Specify a list of student repository URLs to process.
- Run original test files against student repositories.
- Support for specifying the branch to check out in each repository.
- Generate a CSV file containing students' grades.
- Repeat tests a specified number of times to find if there exists bugs related to race condition.



## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.x
- Git and GitHub token
- Golang



## Setup

To use this tool, you need to specify several command line arguments, some of which are optional. Here's a brief overview of the available arguments:

- `--github_token`: Specifies your personal GitHub token for accessing repositories within GitHub Classroom. **This argument is mandatory.**
- `--repo_path`: Defines the path to the file that contains a list of URLs for student repositories. The default value is `repo_list.txt`.
- `--workspace`: The directory where cloned student repositories will be stored. The default setting is `workspace`.
- `--original_tests_dir`: Points to the directory that contains original test files. These files will be used to replace the test scripts in students' repositories. **This argument is mandatory.**
- `--branch_name`: Indicates the name of the branch to be checked out in each student repository. **This argument is mandatory and must be explicitly specified.**
- `--output_file`: The file where the grading report will be saved. Defaults to `output.csv`.
- `--num_trails`: The number of iterations to repeat the tests, aiming to uncover bugs in a multi-threaded environment. The default is set to `1`.
- `--single_student_url`: Direct URL to a single student's repository for processing. Omitting this argument defaults the operation to clone and process all listed student repositories.



## Example

### Testing a Single Student's Repository

To run the autograder on a single student's repository, use the following command:

```bash
python3 autograder.py --github_token=your github token --branch_name=lab1 --single_student_url=https://github.com/uva-cs4740/golabs-JHSUYU.git --original_tests_dir=lab1 --num_trails=1
```

This command specifies the GitHub token, the branch name to check out (`lab1`), the URL of the single student's repository to test, the directory containing the original test files (`lab1`), and sets the number of test iterations to `1`.

### Testing All Students' Repositories

To execute the autograder across all students' repositories listed in the specified repository path file, use the command below:

```bash
python3 autograder.py --github_token=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 --branch_name=lab1 --original_tests_dir=lab1 --num_trails=1
```

This example also uses the provided GitHub token and sets the branch name, the directory for original tests, and the number of test iterations to `1`. By omitting the `--single_student_url` argument, the autograder defaults to processing all student repositories listed in the default or specified repository path file.