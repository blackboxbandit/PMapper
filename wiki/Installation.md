# Installation

## Prerequisites

| Requirement | Details |
|-------------|---------|
| **Python** | 3.5 or higher |
| **pip** | Python package manager |
| **Graphviz** | Required for visualization (`dot` executable) |

### Installing Graphviz

```bash
# macOS
brew install graphviz

# Ubuntu / Debian
sudo apt install graphviz

# Amazon Linux / CentOS / RHEL
sudo yum install graphviz

# Windows
# Download from https://graphviz.org/download/
```

---

## Option 1: Install from PyPI (Recommended)

```bash
pip install principalmapper
```

This installs the `pmapper` command-line tool and the `principalmapper` Python library.

### Verify installation

```bash
pmapper -h
```

---

## Option 2: Install from Source

```bash
# Clone the repository
git clone git@github.com:nccgroup/PMapper.git

# Install with pip
cd PMapper
pip install .
```

### Development install (editable)

```bash
cd PMapper
pip install -e .
```

---

## Option 3: Docker

```bash
# Clone and build
git clone git@github.com:nccgroup/PMapper.git
cd PMapper
docker build -t pmapper .
docker run -it pmapper
```

### Passing AWS Credentials to Docker

**Option A: Environment variables**
```bash
docker run -it \
  -e AWS_ACCESS_KEY_ID="AKIA..." \
  -e AWS_SECRET_ACCESS_KEY="..." \
  -e AWS_SESSION_TOKEN="..." \
  pmapper
```

**Option B: Mount credentials directory**
```bash
docker run -it \
  -v ~/.aws:/root/.aws:ro \
  -e AWS_CONFIG_FILE=/root/.aws/config \
  -e AWS_SHARED_CREDENTIALS_FILE=/root/.aws/credentials \
  pmapper
```

---

## Python Dependencies

Automatically installed by pip:

| Package | Purpose |
|---------|---------|
| `botocore` | AWS API interactions |
| `pydot` | Graph generation (DOT format) |
| `packaging` | Version handling |
| `python-dateutil` | Date parsing |

---

## IAM Permissions Required

The AWS credentials used to create a graph need **read-only** access to IAM and related services. At minimum:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "iam:Get*",
                "iam:List*",
                "sts:GetCallerIdentity",
                "ec2:DescribeInstances",
                "lambda:ListFunctions",
                "lambda:GetPolicy",
                "s3:GetBucketPolicy",
                "sns:GetTopicAttributes",
                "sqs:GetQueueAttributes",
                "kms:GetKeyPolicy",
                "kms:ListKeys",
                "kms:ListAliases",
                "sagemaker:ListNotebookInstances",
                "codebuild:ListProjects",
                "codebuild:BatchGetProjects",
                "cloudformation:ListStacks",
                "autoscaling:DescribeAutoScalingGroups",
                "autoscaling:DescribeLaunchConfigurations",
                "ssm:DescribeInstanceInformation",
                "secretsmanager:ListSecrets"
            ],
            "Resource": "*"
        }
    ]
}
```

For Organizations support, also add:

```json
{
    "Effect": "Allow",
    "Action": [
        "organizations:Describe*",
        "organizations:List*"
    ],
    "Resource": "*"
}
```

---

[← Home](Home) | [Command Reference →](Command-Reference)
