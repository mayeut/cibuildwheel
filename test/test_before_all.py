from __future__ import annotations

import subprocess
import sys
import textwrap

import pytest

from . import test_projects, utils

project_with_before_build_asserts = test_projects.new_c_project(
    setup_py_add=textwrap.dedent(
        r"""
        # assert that the Python version as written to text_info.txt in the CIBW_BEFORE_ALL step
        # is the same one as is currently running.
        with open("text_info.txt") as f:
            stored_text = f.read()
        print("## stored text: " + stored_text)
        parts = stored_text.split("+")
        assert len(parts) == 3
        assert parts[0] == "cpython"
        if sys.implementation.name == "cpython":
            assert sys.hexversion != int(parts[1])
        assert parts[2] == "sample text 123"
        """
    )
)


def test(tmp_path):
    project_dir = tmp_path / "project"
    project_with_before_build_asserts.generate(project_dir)

    with (project_dir / "text_info.txt").open(mode="w") as ff:
        print("dummy text", file=ff)

    # we want to limit the number of builds to speed-up tests
    builds = ["pp310"]  # always one version of PyPy
    if utils.platform == "linux":
        # Linux uses cp38 as a global python
        builds.append("cp312")
    else:
        # use a CPython version that's not running cibuildwheel
        for minor in range(12, 8, -1):
            if (3, minor) != sys.version_info[:2]:
                builds.append(f"cp3{minor}")
                break
    assert len(builds) == 2

    # build the wheels
    before_all_command = '''python -ISc "import os, sys;open('{project}/text_info.txt', 'w').write(f'{sys.implementation.name}+{sys.hexversion}+sample text '+os.environ.get('TEST_VAL', ''))"'''
    actual_wheels = utils.cibuildwheel_run(
        project_dir,
        add_env={
            "CIBW_BUILD": " ".join(f"{build}-*" for build in builds),
            # write python version information to a temporary file, this is
            # checked in setup.py
            "CIBW_BEFORE_ALL": before_all_command,
            "CIBW_BEFORE_ALL_LINUX": f'{before_all_command} && python -ISc "import sys; assert sys.version_info >= (3, 6)"',
            "CIBW_ENVIRONMENT": "TEST_VAL='123'",
        },
    )

    # also check that we got the right wheels
    (project_dir / "text_info.txt").unlink()
    expected_wheels = [
        w for w in utils.expected_wheels("spam", "0.1.0") if any(build in w for build in builds)
    ]
    assert set(actual_wheels) == set(expected_wheels)


def test_failing_command(tmp_path):
    project_dir = tmp_path / "project"
    test_projects.new_c_project().generate(project_dir)

    with pytest.raises(subprocess.CalledProcessError):
        utils.cibuildwheel_run(
            project_dir,
            add_env={
                "CIBW_BEFORE_ALL": "false",
                "CIBW_BEFORE_ALL_WINDOWS": "exit /b 1",
            },
        )


def test_cwd(tmp_path):
    project_dir = tmp_path / "project"
    test_projects.new_c_project().generate(project_dir)

    actual_wheels = utils.cibuildwheel_run(
        project_dir,
        add_env={
            "CIBW_BEFORE_ALL": f'''python -c "import os; assert os.getcwd() == {str(project_dir)!r}"''',
            "CIBW_BEFORE_ALL_LINUX": '''python -c "import os; assert os.getcwd() == '/project'"''',
        },
        single_python=True,
    )

    expected_wheels = utils.expected_wheels("spam", "0.1.0", single_python=True)
    assert set(actual_wheels) == set(expected_wheels)
