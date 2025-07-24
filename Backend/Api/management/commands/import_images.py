
from django.core.management.base import BaseCommand
from Api.models import Person, PersonImages
from django.utils.text import slugify
import face_recognition
from django.conf import settings
import numpy as np
import os
import shutil

class Command(BaseCommand):
    help = 'Imports images from a directory to the database'
    def add_arguments(self, parser):
        parser.add_argument('directory', type=str, help='Directory containing images')

    def handle(self, *args, **kwargs):
        directory = kwargs['directory']
        self.import_images(directory)

    def import_images(self, directory):
        media_root = settings.MEDIA_ROOT
        for filename in os.listdir(directory):
            if filename.endswith('.jpg') or filename.endswith('.png'):
                person_name = os.path.splitext(filename)[0] 
                image_path = os.path.join(directory, filename)
                try:
                    img = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(img)[0].tolist()
                    person, created = Person.objects.get_or_create(name=person_name)
                    dest_path = os.path.join(media_root, 'database', filename)
                    shutil.copyfile(image_path, dest_path)
                    relative_path = os.path.join('database', filename)
                    person_image = PersonImages.objects.create(person=person, image=relative_path,encoding=face_encodings)
                    self.stdout.write(self.style.SUCCESS(f'Successfully imported {filename} for {person_name}'))
                except Exception as error:
                    self.stdout.write(self.style.WARNING(f'No face Detected {filename} for {person_name} error {error}'))
