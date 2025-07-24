from django.core.management.base import BaseCommand
from Api.models import Roles

class Command(BaseCommand):
    help = 'Load predefined roles into the database'

    def handle(self, *args, **options):
        predefined_roles = ['SUPERADMIN', 'LINE', 'FACE', 'AREA']
        for role_name in predefined_roles:
            Roles.objects.get_or_create(name=role_name)
        self.stdout.write(self.style.SUCCESS('Roles loaded successfully'))
        