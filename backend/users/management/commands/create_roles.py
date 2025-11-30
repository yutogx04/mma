from django.core.management.base import BaseCommand
from users.permissions import RolePermissions

class Command(BaseCommand):
    help = 'Create default roles and permissions'
    
    def handle(self, *args, **options):
        self.stdout.write('Creating roles and permissions...')
        
        try:
            RolePermissions.setup_roles_and_permissions()
            self.stdout.write(
                self.style.SUCCESS('Successfully created roles and permissions')
            )
            # Product permissions
            from django.contrib.auth.models import Group
            groups = Group.objects.all()
            for group in groups:
                perm_count = group.permissions.count()
                self.stdout.write(
                f' - {group.name}: {perm_count} permissions'
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating roles: {str(e)}')
            )