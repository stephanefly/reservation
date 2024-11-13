from ftplib import FTP, error_perm
from app.models import EventTemplate, Event
from myselfiebooth.settings import FTP_SERVER, FTP_PORT, FTP_USER, FTP_PASS, PREPA_EVENT_PATH, NAS_EVENT_PATH
from app.module.tools.rennaming import normalized_directory_name
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
import os


class FTPStorage(Storage):
    def __init__(self, hostname, username, password, prepa_event_path, nas_event_path, port):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.prepa_event_path = prepa_event_path
        self.nas_event_path = nas_event_path
        self.port = port

    def _connect(self):
        ftp = FTP()
        ftp.connect(self.hostname, self.port, timeout=10)
        ftp.login(self.username, self.password)
        return ftp

    def _create_event_repository(self, event):
        directory_name = normalized_directory_name(event)
        ftp = self._connect()
        path = os.path.join(self.prepa_event_path, directory_name).replace("\\", "/")

        try:
            ftp.cwd(path)  # Vérifier si le répertoire existe
        except error_perm:
            try:
                ftp.mkd(path)  # Créer le répertoire
            except Exception as e:
                raise ValueError(f"Unable to create directory '{directory_name}': {str(e)}")
        finally:
            ftp.quit()

        event_template, _ = EventTemplate.objects.update_or_create(
            pk=event.event_template.pk if event.event_template else None,
            defaults={'directory_name': directory_name}
        )
        event.event_template = event_template
        event.save()
        return directory_name

    def _rename_event_repository(self, event, new_directory_name):
        old_directory_name = event.event_template.directory_name
        ftp = self._connect()
        old_path = os.path.join(self.prepa_event_path, old_directory_name).replace("\\", "/")
        new_path = os.path.join(self.prepa_event_path, new_directory_name).replace("\\", "/")

        try:
            ftp.cwd(old_path)  # Vérifier l'existence de l'ancien répertoire
            ftp.rename(old_path, new_path)  # Renommer le répertoire
        except error_perm:
            raise ValueError(f"Le répertoire {old_path} n'existe pas et ne peut pas être renommé.")
        except Exception as e:
            raise ValueError(f"Erreur lors du renommage du répertoire : {str(e)}")
        finally:
            ftp.quit()

        event.event_template.directory_name = new_directory_name
        event.event_template.save()
        event.save()

    def _save_png(self, image, event_id):
        if not image.name.lower().endswith('.png'):
            raise ValueError('Only PNG files are allowed for upload')

        ftp = self._connect()
        event = Event.objects.get(pk=event_id)

        if not event.event_template:
            event_template = EventTemplate(statut=False)
            event_template.save()
            event.event_template = event_template
            event.save()

        if not event.event_template.directory_name:
            self._create_event_repository(event)

        increment = event.event_template.num_template
        file_name = f"MySelfieBooth-{event.event_template.directory_name}-{increment}.png"
        event.event_template.num_template += 1
        event.event_template.save()

        prepa_event_path = self.prepa_event_path.replace("\\", "/")
        directory_name = event.event_template.directory_name.replace("\\", "/")
        file_path = f"{prepa_event_path}/{directory_name}/{file_name}"

        try:
            ftp.storbinary(f'STOR {file_path}', image.file)
        except Exception as e:
            raise ValueError(f"Erreur lors du transfert du fichier : {str(e)}")
        finally:
            ftp.quit()

        event.event_template.image_name = file_name
        event.event_template.save()
        event.save()

        return file_path

    def _open(self, name, mode='rb'):
        ftp = self._connect()
        path = os.path.join(self.prepa_event_path, name).replace("\\", "/")
        file_content = ContentFile()

        try:
            ftp.retrbinary(f"RETR {path}", file_content.write)
        finally:
            ftp.quit()

        return file_content

    def exists(self, name):
        ftp = self._connect()
        path = os.path.join(self.prepa_event_path, name).replace("\\", "/")
        try:
            ftp.size(path)
            return True
        except error_perm:
            return False
        finally:
            ftp.quit()

    def _get_last_image(self, event_id):
        ftp = self._connect()
        event = Event.objects.get(pk=event_id)
        prepa_event_path = self.prepa_event_path.replace("\\", "/")
        directory_name = event.event_template.directory_name.replace("\\", "/")
        file_name = event.event_template.image_name
        file_path = f"{prepa_event_path}/{directory_name}/{file_name}"

        file_content = ContentFile()

        try:
            ftp.retrbinary(f"RETR {file_path}", file_content.write)
        finally:
            ftp.quit()

        return file_content, file_name


# Configuration des informations NAS
FTP_STORAGE = FTPStorage(
    hostname=FTP_SERVER,
    username=FTP_USER,
    password=FTP_PASS,
    prepa_event_path=PREPA_EVENT_PATH,
    nas_event_path=NAS_EVENT_PATH,
    port=FTP_PORT
)
