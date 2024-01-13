# Using Git To Host Your Python Packages (For Data Engineers)

## Introduction
Most ETL pipelines have to satisfy the same requirements
- Extract from source.
- Validate extracted data.
- Perform transformations.
- Load results into a destination.
The details may differ across pipelines, but the general steps are the same. 

To avoid a buildup of code duplication, a data team may benefit from creating a Python package for shared functionality (e.g., loading data into Snowflake). However, publishing code to PyPI isn't always an option for security reasons.

Another option is using a git repository to host a package that contains reusable pipeline code. You could then `pip install` that package in any pipeline that needs it.

## Getting started

### Prerequisites

I'll be using Poetry to manage this project's dependencies and version. I recommend installing Poetry with `pipx`, but there are other options.

https://python-poetry.org/docs/#installation

### Creating the package

Let's keep things simple. Our package will contain a function to load data into Snowflake.

```python
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
from snowflake.extensions import SnowflakeConnection


def load_to_snowflake(
    conn: SnowflakeConnection,
    df: pd.DataFrame,
    table_name: str
) -> None:
    """
    Use the write_pandas function to load data into Snowflake.
    """
    write_pandas(
        conn=conn,
        df=df,
        table_name=table_name,
        auto_create_table=True,
        overwrite=True
    )

    return

```

We do this using the `write_pandas` method provided by the Snowflake library. Behind the scenes, `write_pandas` saves a data frame to Parquet files and uploads that to Snowflake. Also, we ensure the target table is dropped and recreated if it already exists.

### Continuous Integration

Changes made to our package should go through a series of quality checks before making it to production. We can automate these using a Github Actions workflow that lints, type checks, and runs unit tests.

```yaml
name: CI Checks

on:
  pull_request:
    types:
      - opened
      - closed
      - synchronize
    branches:
      - main

jobs:
  checks:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      
      - name: Install Poetry
        uses: snok/install-poetry@v1
        with:
          virtualenvs-create: true
          virtualenvs-in-project: true
      
      - name: Install dependencies
        run: poetry install --no-interaction --no-root
      
      - name: Run Linter
        run: poetry run flake8 blogs_python_github_packages  
      
      - name: Run Type Checker
        run: poetry run mypy blogs_python_github_packages  
      
      - name: Run Tests
        run: poetry run pytest --cov=blogs_python_github_packages --suppress-no-test-exit-code
```

In case you aren't too familiar with Github Actions, the above workflow first checks out our repository, installs Python version 3.12, and installs `poetry`. We then use `poetry` to run the linter, type checker, and tests.

Some of the steps in our workflow require additional libraries to be installed.
- `Run Linter` requires `flake8`.
- `Run Type Checker` requires `mypy` and `pandas-stub`
- `Run Tests` requires `pytest`, `pytest-cov`, and `pytest-custom-exit-code`.

We will also need `snowflake-connector-python[pandas]` to execute the functions in our package. Not only can we easily install these libraries using `poetry`, we can also set some libraries as `dev` dependencies. Run the following command from the root of the project (where your `pyproject.toml` file is located at).

- `poetry add flake8 --group dev`
- `poetry add mypy --group dev`
- `poetry add pandas-stub --group dev`
- `poetry add pytest --group dev`
- `poetry add pytest-cov --group dev`
- `poetry add pytest-custom-exit-code --group dev`
- `poetry add snowflake-connector-python[pandas]`

You can now create a pull request in Github to trigger the workflow (feel free to change the trigger to `push` if you have trouble creating a PR.)

### SemVer Releases

Once PR checks have passed and we've merged our changes into `main`, we'll want to cut a new release of our package. We use the SemVer convention to tag our releases. Also, don't forget to update the version within the `pyproject.toml` file to match with the release version. 

```toml
...

version = "0.2.0" # we bumped the minor version from 0.1.0

...

```

Now, create another Github Actions workflow to automate the release

```yaml
name: Release

on:
  workflow_dispatch:
    inputs:
      semver:
        description: 'Which version you want to increment? Use MAJOR, MINOR or PATCH'
        required: true
        default: 'PATCH'

jobs:
  release:
    name: 'Release'
    runs-on: 'ubuntu-latest'

    steps:
      # Checkout sources
      - name: 'Checkout'
        uses: actions/checkout@v2

      - uses: 'rui-costa/action-automatic-semver-releases@v1.1.1'
        with:
          TOKEN: '${{ secrets.RELEASES_TOKEN }}'
          SEMVER: '${{ github.event.inputs.semver }}'

```

This workflows was generated by the [Automatic SemVer Release](https://github.com/marketplace/actions/automatic-semver-release) Action. You will need to create a personal access token and add that as a secret in the package's github repository.

Unlike the CI workflow, this one is triggered manually. This is done by visiting the Actions tab in Github, locating the `Release` workflow, and clicking the `run workflow` drop down.

![alt text](https://github.com/jduran9987/blogs-python-github-packages/images/release.png?raw=true)


