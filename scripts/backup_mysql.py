#!/usr/bin/env python3
"""Sauvegarde MySQL du CRM, sans modifier la base ni exposer ses identifiants."""

import argparse
import datetime as dt
import gzip
import hashlib
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

PREFIX = "reservation-mysql-"


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def check_sql_gzip(path):
    """Lit tout le gzip (CRC inclus) et refuse un export manifestement vide."""
    total = 0
    seen = False
    tail = b""
    with gzip.open(path, "rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            total += len(block)
            joined = tail + block
            if any(token in joined for token in (b"CREATE TABLE", b"INSERT INTO", b"CREATE VIEW")):
                seen = True
            tail = joined[-32:]
    if total < 128 or not seen:
        raise RuntimeError("Export SQL vide ou sans structure de table : sauvegarde refusee")
    return total


def verify_backup(path):
    path = Path(path)
    checksum_path = Path(str(path) + ".sha256")
    expected = checksum_path.read_text(encoding="ascii").strip().split()
    if len(expected) != 2 or expected[1] != path.name:
        raise RuntimeError("Fichier de controle SHA256 invalide")
    if sha256_file(path) != expected[0]:
        raise RuntimeError("Empreinte SHA256 incorrecte")
    return check_sql_gzip(path)


def quote_mysql_option(value):
    value = str(value)
    if "\n" in value or "\r" in value or "\x00" in value:
        raise ValueError("Caractere non autorise dans un parametre MySQL")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def config_file_for_dump(database, temporary_dir):
    """Creer un fichier temporaire en mode 0600, jamais de mot de passe en argument."""
    if not database.get("NAME") or not database.get("USER"):
        raise RuntimeError("Nom ou utilisateur MySQL absent de la configuration Django")
    options = database.get("OPTIONS") or {}
    if options.get("read_default_file") and not database.get("PASSWORD"):
        raise RuntimeError("Identifiants dans read_default_file : adapter le script avant usage")
    path = Path(temporary_dir) / "mysql-client.cnf"
    fields = {"user": database["USER"], "password": database.get("PASSWORD") or ""}
    host = database.get("HOST") or ""
    if host.startswith("/"):
        fields["socket"] = host
    elif host:
        fields["host"] = host
    if database.get("PORT"):
        fields["port"] = database["PORT"]
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    with os.fdopen(os.open(path, flags, 0o600), "w", encoding="utf-8") as handle:
        handle.write("[client]\n")
        for key, value in fields.items():
            handle.write(key + "=" + quote_mysql_option(value) + "\n")
    return path


def load_database_config():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myselfiebooth.settings")
    import django
    django.setup()
    from django.conf import settings
    database = settings.DATABASES["default"]
    if "mysql" not in database.get("ENGINE", "").lower():
        raise RuntimeError("La base Django principale n'est pas MySQL")
    return database


def prepare_directory(path):
    path = Path(path).expanduser()
    project = Path(__file__).resolve().parents[1]
    if path.is_symlink() or path.resolve().is_relative_to(project):
        raise RuntimeError("Refus d'ecrire les sauvegardes dans un lien ou le depot Git")
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise RuntimeError("Le dossier de sauvegarde doit avoir les permissions 0700")
    return path


def create_backup(database, destination):
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = destination / (PREFIX + now + ".sql.gz")
    partial = Path(str(target) + ".part")
    checksum_path = Path(str(target) + ".sha256")
    with tempfile.TemporaryDirectory(prefix="crm-db-credentials-") as temporary:
        credential_file = config_file_for_dump(database, temporary)
        command = [
            "mysqldump", "--defaults-extra-file=" + str(credential_file),
            "--single-transaction", "--quick", "--triggers", "--hex-blob",
            "--no-tablespaces", "--set-gtid-purged=OFF", str(database["NAME"]),
        ]
        try:
            with tempfile.TemporaryFile(mode="w+b") as errors:
                with open(partial, "xb") as raw:
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=errors)
                    try:
                        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
                            shutil.copyfileobj(process.stdout, compressed, length=1024 * 1024)
                    except Exception:
                        process.kill()
                        raise
                    finally:
                        process.stdout.close()
                        exit_code = process.wait()
                if exit_code:
                    raise RuntimeError("mysqldump a echoue (code %s) ; archive rejetee" % exit_code)
            uncompressed_size = check_sql_gzip(partial)
            checksum = sha256_file(partial)
            os.replace(partial, target)
            with open(checksum_path, "x", encoding="ascii") as output:
                output.write(checksum + "  " + target.name + "\n")
            return target, uncompressed_size
        except Exception:
            partial.unlink(missing_ok=True)
            if target.exists() and not checksum_path.exists():
                target.unlink()
            raise


def prune_old_backups(directory, days, current):
    if days <= 0:
        return 0
    cutoff = dt.datetime.now(dt.timezone.utc).timestamp() - days * 86400
    removed = 0
    for archive in directory.glob(PREFIX + "*.sql.gz"):
        checksum = Path(str(archive) + ".sha256")
        if archive != current and archive.stat().st_mtime < cutoff and checksum.is_file():
            archive.unlink()
            checksum.unlink()
            removed += 1
    return removed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", type=Path, help="Verifier une archive existante sans acceder a MySQL")
    parser.add_argument("--output-dir", type=Path, default=Path.home() / "private-backups" / "reservation")
    parser.add_argument("--retain-days", type=int, default=30, help="0 = aucune suppression automatique")
    args = parser.parse_args(argv)
    os.umask(0o077)
    try:
        if args.verify:
            size = verify_backup(args.verify)
            print("OK : archive et SHA256 valides (%s octets SQL)" % size)
            return 0
        if args.retain_days < 0:
            raise ValueError("--retain-days doit etre positif")
        directory = prepare_directory(args.output_dir)
        target, size = create_backup(load_database_config(), directory)
        verify_backup(target)
        removed = prune_old_backups(directory, args.retain_days, target)
        print("OK : %s (%s octets SQL, verification gzip et SHA256)" % (target, size))
        print("Anciennes archives supprimees : %s" % removed)
        return 0
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print("ERREUR SAUVEGARDE : %s" % error, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
