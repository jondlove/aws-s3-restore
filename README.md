# AWS S3 Restore
Restore a directory structure from Amazon AWS S3

This script allows you to restore files from the remote AWS S3 Bucket from a specified number of days ago, back into the current directory.

## How To Use
- Copy `src/aws-s3-restore.conf.example` to `src/aws-s3-restore.conf`
- Add your AWS credentials to `src/aws-s3-restore.conf`
- In your shell, run `source src/bin/activate` to activate virtualenv
	- For more on VirtualEnv, refer to http://docs.python-guide.org/en/latest/dev/virtualenvs/
- Install the PIP requirements with `pip install -r src/requirements.txt`
- To run the script use `python src/aws-s3-restore.py`