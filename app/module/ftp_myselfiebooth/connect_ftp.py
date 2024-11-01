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
        self.transport = None  # Ajouter transport comme attribut pour une gestion correcte

    def _connect(self):
        """Établit une connexion SFTP et retourne un client SFTP."""
        try:
            self.transport = paramiko.Transport((self.hostname, self.port))
            self.transport.connect(username=self.username, password=self.password)
            return paramiko.SFTPClient.from_transport(self.transport)
        except Exception as e:
            raise ConnectionError(f"Impossible de se connecter au serveur SFTP : {str(e)}")

    def close(self):
        """Ferme la connexion SFTP proprement."""
        if self.transport:
            self.transport.close()

    def _create_event_repository(self, event):
        """Crée un répertoire pour l'événement sur le serveur SFTP."""
        directory_name = normalized_directory_name(event)
        sftp = self._connect()
        path = os.path.join(self.prepa_event_path, directory_name).replace("\\", "/")
        try:
            sftp.stat(path)  # Vérifier si le répertoire existe déjà
        except FileNotFoundError:
            try:
                sftp.mkdir(path)
            except Exception as e:
                raise ValueError(f"Impossible de créer le répertoire '{directory_name}': {str(e)}")
        finally:
            sftp.close()

        # Crée ou met à jour l'EventTemplate pour l'événement
        event_template, created = EventTemplate.objects.update_or_create(
            pk=event.event_template.pk if event.event_template else None,
            defaults={'directory_name': directory_name}
        )
        event.event_template = event_template
        event.save()
        return directory_name

    def _renname_event_repository(self, event, new_directory_name):
        """Renomme le répertoire de l'événement sur le serveur SFTP."""
        old_directory_name = event.event_template.directory_name
        sftp = self._connect()
        old_path = os.path.join(self.prepa_event_path, old_directory_name).replace("\\", "/")
        new_path = os.path.join(self.prepa_event_path, new_directory_name).replace("\\", "/")

        try:
            sftp.stat(old_path)  # Vérifier si l'ancien répertoire existe
            sftp.rename(old_path, new_path)
        except FileNotFoundError:
            raise ValueError(f"Le répertoire {old_path} n'existe pas et ne peut pas être renommé.")
        except Exception as e:
            raise ValueError(f"Erreur lors du renommage du répertoire : {str(e)}")
        finally:
            sftp.close()

        # Met à jour l'EventTemplate avec le nouveau nom de répertoire
        event.event_template.directory_name = new_directory_name
        event.event_template.save()
        event.save()

    def _save_png(self, image, event_id):
        """Enregistre une image PNG dans le répertoire de l'événement."""
        if not image.name.lower().endswith('.png'):
            raise ValueError('Seuls les fichiers PNG sont autorisés pour le téléchargement')

        sftp = self._connect()
        event = Event.objects.get(pk=event_id)

        # Crée ou récupère un EventTemplate associé à l'événement
        if not event.event_template:
            event_template = EventTemplate(statut=False)
            event_template.save()  # Sauvegarder d'abord l'EventTemplate
            event.event_template = event_template
            event.save()  # Ensuite sauvegarder l'événement pour l'association

        if not event.event_template.directory_name:
            self._create_event_repository(event)

        # Incrémentation du nom de fichier
        increment = event.event_template.num_template
        file_name = f"MySelfieBooth-{event.event_template.directory_name}-{increment}.png"
        event.event_template.num_template += 1
        event.event_template.save()

        # Chemin complet pour le fichier sur le NAS
        prepa_event_path = self.prepa_event_path.replace("\\", "/")
        directory_name = event.event_template.directory_name.replace("\\", "/")
        file_path = f"{prepa_event_path}/{directory_name}/{file_name}"

        try:
            with sftp.file(file_path, 'wb') as f:
                f.write(image.read())
        finally:
            sftp.close()

        event.event_template.image_name = file_name
        event.event_template.save()
        event.save()
        return file_path

    def _open(self, name, mode='rb'):
        """Ouvre un fichier sur le NAS en mode lecture."""
        sftp = self._connect()
        path = os.path.join(self.prepa_event_path, name).replace("\\", "/")
        try:
            file_content = sftp.file(path, mode).read()
            return ContentFile(file_content)
        finally:
            sftp.close()

    def exists(self, name):
        """Vérifie si un fichier existe déjà sur le NAS."""
        sftp = self._connect()
        path = os.path.join(self.prepa_event_path, name).replace("\\", "/")
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
            remote_file.close()
            return file_data, file_name
        finally:
            sftp.close()


# Configuration des informations NAS pour une utilisation facile
SFTP_STORAGE = SFTPStorage(
    hostname=FTP_SERVER,
    username=FTP_USER,
    password=FTP_PASS,
    prepa_event_path=PREPA_EVENT_PATH,
    nas_event_path=NAS_EVENT_PATH,
    port=FTP_PORT
)
