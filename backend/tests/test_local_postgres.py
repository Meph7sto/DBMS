import os
import unittest
from pathlib import Path
from unittest import mock

import local_postgres


class LocalPostgresTests(unittest.TestCase):
    def test_find_installation_matches_requested_port(self) -> None:
        root = Path("W:/fake-postgres")

        def fake_exists(path: Path) -> bool:
            return str(path) in {
                str(root / "bin" / "pg_ctl.exe"),
                str(root / "data"),
            }

        with mock.patch(
            "local_postgres._candidate_install_dirs",
            return_value=[root],
        ):
            with mock.patch.dict(
                os.environ,
                {
                    "LOCAL_PG_BIN_DIR": str(root / "bin"),
                    "LOCAL_PG_DATA_DIR": str(root / "data"),
                },
                clear=False,
            ):
                with mock.patch("pathlib.Path.exists", autospec=True, side_effect=fake_exists):
                    with mock.patch("local_postgres._read_configured_port", return_value=5438):
                        installation = local_postgres._find_installation(5438)

        self.assertIsNotNone(installation)
        self.assertEqual(installation.install_dir, root)
        self.assertEqual(installation.data_dir, root / "data")
        self.assertEqual(installation.port, 5438)

    def test_remove_stale_pid_file_when_process_is_missing(self) -> None:
        installation = local_postgres.LocalPostgresInstallation(
            install_dir=Path("W:/fake-postgres"),
            bin_dir=Path("W:/fake-postgres/bin"),
            data_dir=Path("W:/fake-postgres/data"),
            port=5438,
        )
        pid_file = installation.data_dir / "postmaster.pid"

        def fake_exists(path: Path) -> bool:
            return str(path) == str(pid_file)

        with mock.patch("pathlib.Path.exists", autospec=True, side_effect=fake_exists):
            with mock.patch("local_postgres._read_pid", return_value=999999):
                with mock.patch("local_postgres._process_exists", return_value=False):
                    with mock.patch("local_postgres._tcp_ready", return_value=False):
                        with mock.patch("pathlib.Path.unlink", autospec=True) as mocked_unlink:
                            removed = local_postgres._remove_stale_pid_file(
                                installation,
                                5438,
                            )

        self.assertTrue(removed)
        mocked_unlink.assert_called_once_with(pid_file, missing_ok=True)

    def test_ensure_local_postgres_ready_starts_server_when_port_is_closed(self) -> None:
        installation = local_postgres.LocalPostgresInstallation(
            install_dir=Path("W:/fake-postgres"),
            bin_dir=Path("W:/fake-postgres/bin"),
            data_dir=Path("W:/fake-postgres/data"),
            port=5438,
        )
        log_file = installation.data_dir / "log" / "auto-start.log"
        process = mock.Mock()
        process.poll.side_effect = [None, None]

        with mock.patch.dict(
            os.environ,
            {
                "LOCAL_PG_AUTO_START": "1",
                "LOCAL_PG_START_TIMEOUT": "5",
            },
            clear=False,
        ):
            with mock.patch("local_postgres._find_installation", return_value=installation):
                with mock.patch("local_postgres._get_log_file", return_value=log_file):
                    with mock.patch("pathlib.Path.mkdir", autospec=True):
                        with mock.patch(
                            "local_postgres._remove_stale_pid_file",
                            return_value=False,
                        ):
                            with mock.patch(
                                "local_postgres._tcp_ready",
                                side_effect=[False, False, True],
                            ):
                                with mock.patch("local_postgres.time.sleep"):
                                    with mock.patch(
                                        "local_postgres._terminate_helper_process",
                                    ) as mocked_terminate:
                                        with mock.patch(
                                            "local_postgres.subprocess.Popen",
                                            return_value=process,
                                        ) as mocked_popen:
                                            info = local_postgres.ensure_local_postgres_ready(
                                                "localhost",
                                                5438,
                                            )

        self.assertTrue(info["managed"])
        self.assertTrue(info["started"])
        self.assertFalse(info["recovered_stale_pid"])
        self.assertEqual(info["log_file"], str(log_file))
        self.assertEqual(mocked_popen.call_count, 1)
        args = mocked_popen.call_args.args[0]
        self.assertEqual(args[-2:], ["-l", str(log_file)])
        mocked_terminate.assert_called_once_with(process)

    def test_get_log_file_falls_back_to_temp_dir_when_configured_path_is_unwritable(self) -> None:
        installation = local_postgres.LocalPostgresInstallation(
            install_dir=Path("W:/fake-postgres"),
            bin_dir=Path("W:/fake-postgres/bin"),
            data_dir=Path("W:/fake-postgres/data"),
            port=5438,
        )
        configured = Path("W:/fake-postgres/pg_ctl-start.log")
        fallback = Path("C:/Temp/dbms-visual-manager/postgres/pg_ctl-start-5438.log")

        with mock.patch.dict(
            os.environ,
            {"LOCAL_PG_LOG_FILE": str(configured)},
            clear=False,
        ):
            with mock.patch(
                "local_postgres._default_log_file",
                return_value=fallback,
            ):
                with mock.patch(
                    "local_postgres._can_write_log_file",
                    side_effect=lambda path: path == fallback,
                ):
                    log_file = local_postgres._get_log_file(installation)

        self.assertEqual(log_file, fallback)


if __name__ == "__main__":
    unittest.main()
