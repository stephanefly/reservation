"""Tests locaux sans Django, connexion MySQL, ni donnees de production."""
import gzip
import hashlib
import os
import tempfile
import time
import unittest
from pathlib import Path
from scripts import backup_mysql as backup


class BackupMysqlTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def make_backup(self, sql):
        archive = self.directory / "reservation-mysql-test.sql.gz"
        with gzip.open(archive, "wb") as output:
            output.write(sql)
        sha = hashlib.sha256(archive.read_bytes()).hexdigest()
        Path(str(archive) + ".sha256").write_text(sha + "  " + archive.name + "\n")
        return archive

    def test_valid_archive(self):
        archive = self.make_backup(b"CREATE TABLE example (id INT);\n" * 10)
        self.assertGreater(backup.verify_backup(archive), 128)

    def test_tampered_archive(self):
        archive = self.make_backup(b"CREATE TABLE example (id INT);\n" * 10)
        archive.write_bytes(archive.read_bytes() + b"tampered")
        with self.assertRaisesRegex(RuntimeError, "SHA256"):
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

    def test_refuse_repository_as_destination(self):
        with self.assertRaisesRegex(RuntimeError, "depot Git"):
            backup.prepare_directory(Path(__file__).resolve().parents[1] / "backup")

    def test_prune_only_old_verified_archives(self):
        archive = self.make_backup(b"CREATE TABLE example (id INT);\n" * 10)
        os.utime(archive, (time.time() - 40 * 86400,) * 2)
        other = self.directory / "reservation-mysql-latest.sql.gz"
        other.write_bytes(b"recent backup")
        count = backup.prune_old_backups(self.directory, 30, other)
        self.assertEqual(count, 1)
        self.assertFalse(archive.exists())
        self.assertTrue(other.exists())


if __name__ == "__main__":
    unittest.main()
