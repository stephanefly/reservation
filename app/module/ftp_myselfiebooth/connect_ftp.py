import paramiko
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from myselfiebooth.settings import FTP_SERVER, FTP_PORT, FTP_USER, FTP_PASS, PREPA_EVENT_PATH, NAS_EVENT_PATH
from app.models import EventTemplate, Event
from app.module.ftp_myselfiebooth.rennaming import normalize_name
import os
import logging

# Configurer le logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SFTPStorage(Storage):
    def __init__(self, hostname, username, password, prepa_event_path, nas_event_path, port):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.prepa_event_path = prepa_event_path
        self.nas_event_path = nas_event_path
        self.port = port

    def _connect(self):
        """Établit une connexion SFTP."""
        try:
            transport = paramiko.Transport((self.hostname, self.port))
            transport.connect(username=self.username, password=self.password)
            logger.info(f"Connexion SFTP réussie : {self.hostname}:{self.port}")
            return paramiko.SFTPClient.from_transport(transport)
        except Exception as e:
            logger.error(f"Impossible de se connecter au serveur SFTP : {str(e)}")
            raise ConnectionError(f"Impossible de se connecter au serveur SFTP : {str(e)}")

    def _create_event_repository(self, event):
        """Crée un répertoire pour l'événement sur le serveur SFTP."""
        directory_name = normalize_name(event)
        with self._connect() as sftp:
            path = os.path.join(self.prepa_event_path, directory_name).replace("\\", "/")
            try:
                sftp.stat(path)  # Vérifie si le répertoire existe
                logger.info(f"Le répertoire existe déjà : {path}")
            except FileNotFoundError:
                try:
                    sftp.mkdir(path)  # Crée le répertoire
                    logger.info(f"Répertoire créé avec succès : {path}")
                except Exception as e:
                    logger.error(f"Erreur lors de la création du répertoire {path} : {str(e)}")
                    raise ValueError(f"Unable to create directory '{directory_name}': {str(e)}")

        event_template, _ = EventTemplate.objects.update_or_create(
            pk=event.event_template.pk if event.event_template else None,
            defaults={'directory_name': directory_name}
        )
        event.event_template = event_template
        event.save()
        return directory_name

    def _rename_event_repository(self, event, new_directory_name):
        """Renomme le répertoire d'un événement."""
        old_directory_name = event.event_template.directory_name
        with self._connect() as sftp:
            old_path = os.path.join(self.prepa_event_path, old_directory_name).replace("\\", "/")
            new_path = os.path.join(self.prepa_event_path, new_directory_name).replace("\\", "/")

            try:
                sftp.stat(old_path)
                sftp.rename(old_path, new_path)
                logger.info(f"Répertoire renommé : {old_path} -> {new_path}")
            except FileNotFoundError:
                logger.error(f"Le répertoire {old_path} n'existe pas.")
                raise ValueError(f"Le répertoire {old_path} n'existe pas et ne peut pas être renommé.")
            except Exception as e:
                logger.error(f"Erreur lors du renommage du répertoire : {str(e)}")
                raise ValueError(f"Erreur lors du renommage du répertoire : {str(e)}")

        event.event_template.directory_name = new_directory_name
        event.event_template.save()
        event.save()

    def _save_png(self, image, event_id):
        """Enregistre une image PNG dans le répertoire de l'événement."""
        if not image.name.lower().endswith('.png'):
            raise ValueError('Only PNG files are allowed for upload')

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

        with self._connect() as sftp:
            with sftp.file(file_path, 'w') as f:
                f.write(image.read())
                logger.info(f"Image enregistrée avec succès : {file_path}")

        event.event_template.image_name = file_name
        event.event_template.save()
        event.save()

        return file_path

    def _open(self, name, mode='rb'):
        """Ouvre un fichier sur le serveur SFTP."""
        with self._connect() as sftp:
            path = os.path.join(self.prepa_event_path, name).replace("\\", "/")
            try:
                file_content = sftp.file(path, mode).read()
                logger.info(f"Fichier ouvert : {path}")
                return ContentFile(file_content)
            except Exception as e:
                logger.error(f"Erreur lors de l'ouverture du fichier {path} : {str(e)}")
                raise

    def exists(self, name):
        """Vérifie si un fichier existe sur le serveur SFTP."""
        with self._connect() as sftp:
            path = os.path.join(self.prepa_event_path, name).replace("\\", "/")
            try:
                sftp.stat(path)
                logger.info(f"Le fichier existe : {path}")
                return True
            except FileNotFoundError:
                logger.info(f"Le fichier n'existe pas : {path}")
                return False
            except Exception as e:
                logger.error(f"Erreur lors de la vérification de l'existence du fichier {path} : {str(e)}")
                raise

    def _get_last_image(self, event_id):
        """Récupère la dernière image associée à un événement."""
        event = Event.objects.get(pk=event_id)
        prepa_event_path = self.prepa_event_path.replace("\\", "/")
        directory_name = event.event_template.directory_name.replace("\\", "/")
        file_name = event.event_template.image_name
        file_path = f"{prepa_event_path}/{directory_name}/{file_name}"

        with self._connect() as sftp:
            try:
                remote_file = sftp.file(file_path, 'rb')
                file_data = remote_file.read()
                logger.info(f"Image récupérée : {file_path}")
                return file_data, file_name
            except Exception as e:
                logger.error(f"Erreur lors de la récupération de l'image {file_path} : {str(e)}")
                raise


# Configuration de stockage SFTP
SFTP_STORAGE = SFTPStorage(
    hostname=FTP_SERVER,
    username=FTP_USER,
    password=FTP_PASS,
    prepa_event_path=PREPA_EVENT_PATH,
    nas_event_path=NAS_EVENT_PATH,
    port=FTP_PORT
)
