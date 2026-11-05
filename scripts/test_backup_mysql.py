"""Tests isoles : aucune connexion a la base de production."""
import gzip
import hashlib
import io
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import backup_mysql as backup


SQL = b"CREATE TABLE example (id INT);\n" * 10


class BackupMysqlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def make_backup(self, sql=SQL):
        archive = self.directory / "reservation-mysql-test.sql.gz"
        with gzip.open(archive, "wb") as output:
            output.write(sql)
        self.write_checksum(archive)
        return archive

    @staticmethod
    def write_checksum(archive):
        sha = hashlib.sha256(archive.read_bytes()).hexdigest()
        Path(str(archive) + ".sha256").write_text(sha + "  " + archive.name + "\n")

    def test_valid_archive(self):
        self.assertGreater(backup.verify_backup(self.make_backup()), 128)

    def test_tampered_archive_rejected(self):
        archive = self.make_backup()
        archive.write_bytes(archive.read_bytes() + b"tampered")
        with self.assertRaisesRegex(RuntimeError, "SHA256"):
            backup.verify_backup(archive)

    def test_invalid_gzip_rejected_even_if_checksum_matches(self):
        archive = self.make_backup()
        archive.write_bytes(b"invalid gzip")
        self.write_checksum(archive)
        with self.assertRaises(OSError):
            backup.verify_backup(archive)

    def test_missing_checksum_rejected(self):
        archive = self.make_backup()
        Path(str(archive) + ".sha256").unlink()
        with self.assertRaises(FileNotFoundError):
            backup.verify_backup(archive)

    def test_wrong_checksum_filename_rejected(self):
        archive = self.make_backup()
        Path(str(archive) + ".sha256").write_text("a" * 64 + "  another.sql.gz\n")
        with self.assertRaisesRegex(RuntimeError, "invalide"):
            backup.verify_backup(archive)

    def test_empty_dump_rejected(self):
        archive = self.make_backup(b"-- empty database\n")
        with self.assertRaisesRegex(RuntimeError, "vide"):
            backup.verify_backup(archive)

    def test_credentials_escaped_and_private(self):
        database = {"NAME": "user$db", "USER": "user", "PASSWORD": 'abc"def\\ghi', "HOST": "mysql.example", "PORT": 3306}
        path = backup.config_file_for_dump(database, self.directory)
        self.assertIn('password="abc\\"def\\\\ghi"', path.read_text())
        self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_newline_in_credentials_rejected(self):
        with self.assertRaises(ValueError):
            backup.quote_mysql_option("password\ninvalide")

    def test_refuse_repository_as_destination(self):
        with self.assertRaisesRegex(RuntimeError, "depot Git"):
            backup.prepare_directory(Path(__file__).resolve().parents[1] / "backup")

    def test_refuse_world_readable_destination(self):
        destination = self.directory / "unsafe"
        destination.mkdir(mode=0o755)
        destination.chmod(0o755)
        with self.assertRaisesRegex(RuntimeError, "0700"):
            backup.prepare_directory(destination)

    def test_prune_only_old_verified_archives(self):
        archive = self.make_backup()
        os.utime(archive, (time.time() - 40 * 86400,) * 2)
        current = self.directory / "reservation-mysql-latest.sql.gz"
        current.write_bytes(b"recent backup")
        self.assertEqual(backup.prune_old_backups(self.directory, 30, current), 1)
        self.assertFalse(archive.exists())
        self.assertTrue(current.exists())

    def test_no_prune_when_disabled(self):
        archive = self.make_backup()
        os.utime(archive, (time.time() - 40 * 86400,) * 2)
        self.assertEqual(backup.prune_old_backups(self.directory, 0, Path("new")), 0)
        self.assertTrue(archive.exists())

    def test_no_prune_without_checksum(self):
        archive = self.make_backup()
        Path(str(archive) + ".sha256").unlink()
        os.utime(archive, (time.time() - 40 * 86400,) * 2)
        self.assertEqual(backup.prune_old_backups(self.directory, 30, Path("new")), 0)
        self.assertTrue(archive.exists())

    def fake_dump(self, return_code=0):
        commands = []
        class FakeProcess:
            def __init__(self, command, stdout, stderr):
                commands.append(command)
                self.stdout = io.BytesIO(SQL)
            def wait(self):
                return return_code
            def kill(self):
                pass
        return FakeProcess, commands

    def test_full_dump_with_fake_mysql_client(self):
        fake, commands = self.fake_dump()
        database = {"NAME": "user$db", "USER": "user", "PASSWORD": "private-secret", "HOST": "mysql.example"}
        with patch.object(backup.subprocess, "Popen", fake):
            archive, size = backup.create_backup(database, self.directory)
        self.assertGreater(size, 128)
        self.assertGreater(backup.verify_backup(archive), 128)
        self.assertEqual(len(commands), 1)
        self.assertTrue(commands[0][1].startswith("--defaults-extra-file="))
        self.assertTrue(all("private-secret" not in arg for arg in commands[0]))

    def test_failed_mysqldump_never_keeps_partial_archive(self):
        fake, _ = self.fake_dump(return_code=2)
        database = {"NAME": "user$db", "USER": "user", "PASSWORD": "secret", "HOST": "mysql.example"}
        with patch.object(backup.subprocess, "Popen", fake):
            with self.assertRaisesRegex(RuntimeError, "mysqldump"):
                backup.create_backup(database, self.directory)
        self.assertEqual(list(self.directory.glob("*.sql.gz*")), [])
        self.assertEqual(list(self.directory.glob("*.part")), [])


if __name__ == "__main__":
    unittest.main()
