"""
Management command to create roles and permissions
Usage: python manage.py create_roles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import transaction


class Command(BaseCommand):
    help = 'Create user roles (Customer, Vendor, Admin) with their permissions'

    def handle(self, *args, **options):
        self.stdout.write('Creating roles and permissions...')
        
        with transaction.atomic():
            self._create_customer_role()
            self._create_vendor_role()
            self._create_admin_role()
        
        self.stdout.write(self.style.SUCCESS('Roles created successfully!'))

    def _create_customer_role(self):
        """Create Customer role with specific permissions"""
        from products.models import Product, Category
        from orders.models import Order
        from reviews.models import Review
        from payments.models import Payment
        from invoices.models import Invoice
        
        customer_group, created = Group.objects.get_or_create(name='Customers')
        
        customer_permissions = [
            ('view_product', Product),
            ('view_category', Category),
            ('view_order', Order),
            ('add_order', Order),
            ('change_order', Order),
            ('delete_order', Order),
            ('view_review', Review),
            ('add_review', Review),
            ('change_review', Review),
            ('delete_review', Review),
            ('view_payment', Payment),
            ('add_payment', Payment),
            ('view_invoice', Invoice),
        ]
        
        self._assign_permissions(customer_group, customer_permissions)
        self.stdout.write(f'  ✓ Customer role {"created" if created else "updated"}')

    def _create_vendor_role(self):
        """Create Vendor role with product management permissions"""
        from products.models import Product, Category
        from orders.models import Order
        from reviews.models import Review
        
        vendor_group, created = Group.objects.get_or_create(name='Vendors')
        
        vendor_permissions = [
            ('add_product', Product),
            ('change_product', Product),
            ('delete_product', Product),
            ('view_product', Product),
            ('view_category', Category),
            ('view_order', Order),
            ('change_order', Order),
            ('view_shop', 'shop.Shop'),
            ('change_shop', 'shop.Shop'),
            ('view_review', Review),
        ]
        
        self._assign_permissions(vendor_group, vendor_permissions)
        self.stdout.write(f'  ✓ Vendor role {"created" if created else "updated"}')

    def _create_admin_role(self):
        """Create Admin role with all permissions"""
        admin_group, created = Group.objects.get_or_create(name='Administrators')
        admin_group.permissions.set(Permission.objects.all())
        self.stdout.write(f'  ✓ Admin role {"created" if created else "updated"}')

    def _assign_permissions(self, group, permission_list):
        """Assign list of permissions to a group"""
        for perm_codename, model in permission_list:
            try:
                if isinstance(model, str):
                    app_label, model_name = model.split('.')
                    content_type = ContentType.objects.get(
                        app_label=app_label,
                        model=model_name.lower()
                    )
                else:
                    content_type = ContentType.objects.get_for_model(model)
                
                permission = Permission.objects.get(
                    codename=perm_codename,
                    content_type=content_type
                )
                group.permissions.add(permission)
            except (ContentType.DoesNotExist, Permission.DoesNotExist):
                self.stdout.write(
                    self.style.WARNING(f'  ! Permission {perm_codename} not found')
                )