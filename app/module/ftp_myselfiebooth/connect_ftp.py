from app.models import EventTemplate, Event
from myselfiebooth.settings import FTP_SERVER, FTP_PORT, FTP_USER, FTP_PASS, PREPA_EVENT_PATH, NAS_EVENT_PATH
from app.module.tools.rennaming import normalized_directory_name
import paramiko
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
import os

class SFTPStorage(Storage):
    def __init__(self, hostname, username, password, prepa_event_path, nas_event_path, port):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.prepa_event_path = prepa_event_path
        self.nas_event_path = nas_event_path
        self.port = port

    def _connect(self):
        transport = paramiko.Transport((self.hostname, self.port))
        transport.connect(username=self.username, password=self.password)
        return paramiko.SFTPClient.from_transport(transport)

    def _create_event_repository(self, event):
        directory_name = normalized_directory_name(event)
        sftp = self._connect()
        path = os.path.join(self.prepa_event_path, directory_name)

        try:
            sftp.stat(path)  # Vérifier si le répertoire existe
        except FileNotFoundError:
            try:
                sftp.mkdir(path)  # Créer le répertoire
            except Exception as e:
                raise ValueError(f"Unable to create directory '{directory_name}': {str(e)}")
        finally:
            sftp.close()

        event_template, _ = EventTemplate.objects.update_or_create(
            pk=event.event_template.pk if event.event_template else None,
            defaults={'directory_name': directory_name}
        )
        event.event_template = event_template
        event.save()
        return directory_name

    def _rename_event_repository(self, event, new_directory_name):
        old_directory_name = event.event_template.directory_name
        sftp = self._connect()
        old_path = os.path.join(self.prepa_event_path, old_directory_name)
        new_path = os.path.join(self.prepa_event_path, new_directory_name)

        try:
            sftp.stat(old_path)  # Vérifier l'existence de l'ancien répertoire
            sftp.rename(old_path, new_path)  # Renommer le répertoire
        except FileNotFoundError:
            raise ValueError(f"Le répertoire {old_path} n'existe pas et ne peut pas être renommé.")
        except Exception as e:
            raise ValueError(f"Erreur lors du renommage du répertoire : {str(e)}")
        finally:
            sftp.close()

        event.event_template.directory_name = new_directory_name
        event.event_template.save()
        event.save()

    def _save_png(self, image, event_id):
        if not image.name.lower().endswith('.png'):
            raise ValueError('Only PNG files are allowed for upload')

        sftp = self._connect()
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

        with sftp.file(file_path, 'w') as f:
            f.write(image.read())

        sftp.close()
        event.event_template.image_name = file_name
        event.event_template.save()
        event.save()

        return file_path

    def _open(self, name, mode='rb'):
        sftp = self._connect()
        path = os.path.join(self.base_path, name)
        file_content = sftp.file(path, mode).read()
        sftp.close()
        return ContentFile(file_content)

    def exists(self, name):
        sftp = self._connect()
        path = os.path.join(self.base_path, name)
        try:
            sftp.stat(path)
            return True
        except FileNotFoundError:
            return False
        finally:
            sftp.close()

    def _get_last_image(self, event_id):
        """Récupère la dernière image associée à un événement."""
        sftp = self._connect()
        event = Event.objects.get(pk=event_id)
        prepa_event_path = self.prepa_event_path.replace("\\", "/")
        directory_name = event.event_template.directory_name.replace("\\", "/")
        file_name = event.event_template.image_name
        file_path = f"{prepa_event_path}/{directory_name}/{file_name}"

        try:
            remote_file = sftp.file(file_path, 'rb')
            file_data = remote_file.read()
            return file_data, file_name
        finally:
            sftp.close()


# Configuration des informations NAS
SFTP_STORAGE = SFTPStorage(
    hostname=FTP_SERVER,
    username=FTP_USER,
    password=FTP_PASS,
    prepa_event_path=PREPA_EVENT_PATH,
    nas_event_path=NAS_EVENT_PATH,
    port=FTP_PORT
)