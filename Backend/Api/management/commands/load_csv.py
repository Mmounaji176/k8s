
from django.core.management.base import BaseCommand
from Api.models import Person, PersonImages
import face_recognition
from django.conf import settings
import os
import shutil
import pandas as pd
class Command(BaseCommand):
    help = 'Imports images from a csv file to the database'
    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='csv file containing images')

    def handle(self, *args, **kwargs):
        csv_file = kwargs['csv_file']
        self.import_images(csv_file)

    def import_images(self, csv_file):
        media_root = settings.MEDIA_ROOT
        data = pd.read_excel(csv_file)

        for index , name in enumerate(data.NOM):
                person_name = name + " " + data.Prenom[index]
                cni         = data.CNI[index]
                image_path  = data.Photo[index]
                try:
                    img = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(img)[0].tolist()
                    person, created = Person.objects.get_or_create(name=person_name, cin=cni)
                    dest_path = os.path.join(media_root, 'database', image_path)
                    shutil.copyfile(image_path, dest_path)
                    relative_path = os.path.join('database', image_path)
                    person_image = PersonImages.objects.create(person=person, image=relative_path,encoding=face_encodings)
                    self.stdout.write(self.style.SUCCESS(f'Successfully imported {image_path} for {person_name}'))
                except Exception as error:
                    self.stdout.write(self.style.WARNING(f'No face Detected {image_path} for {person_name} error {error}'))