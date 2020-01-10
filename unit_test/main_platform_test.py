import pytest

import sys

from cibuildwheel.__main__ import main

from main_util_fixtures import MOCK_PROJECT_DIR, mock_protection, fake_project_dir, platform, intercepted_build_args


def test_unknown_platform_non_ci(monkeypatch, capsys):
    monkeypatch.delenv('CI', raising=False)
    monkeypatch.delenv('BITRISE_BUILD_NUMBER', raising=False)
    monkeypatch.delenv('AZURE_HTTP_USER_AGENT', raising=False)
    monkeypatch.delenv('GITHUB_WORKFLOW', raising=False)

    with pytest.raises(SystemExit) as exit:
        main()
        assert exit.value.code == 2
    _, err = capsys.readouterr()

    assert 'cibuildwheel: Unable to detect platform.' in err
    assert 'cibuildwheel should run on your CI server' in err


def test_unknown_platform_on_ci(monkeypatch, capsys):
    monkeypatch.setenv('CI', 'true')
    monkeypatch.setattr(sys, 'platform', 'nonexistent')

    with pytest.raises(SystemExit) as exit:
        main()
        assert exit.value.code == 2
    _, err = capsys.readouterr()

    assert 'cibuildwheel: Unable to detect platform from "sys.platform"' in err


def test_unknown_platform(monkeypatch, capsys):
    monkeypatch.setenv('CIBW_PLATFORM', 'nonexistent')

    with pytest.raises(SystemExit) as exit:
        main()
    _, err = capsys.readouterr()

    assert exit.value.code == 2
    assert 'cibuildwheel: Unsupported platform: nonexistent' in err


def test_platform_argument(platform, intercepted_build_args, monkeypatch):
    monkeypatch.setenv('CIBW_PLATFORM', 'nonexistent')
    monkeypatch.setattr(sys, 'argv', sys.argv + ['--platform', platform])

    main()

    assert intercepted_build_args.kwargs['project_dir'] == MOCK_PROJECT_DIR


def test_platform_environment(platform, intercepted_build_args, monkeypatch):
    main()

    assert intercepted_build_args.kwargs['project_dir'] == MOCK_PROJECT_DIR
