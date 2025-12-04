"""
Management command to create product categories
Usage: python manage.py create_categories
"""
from django.core.management.base import BaseCommand
from products.models import Category


class Command(BaseCommand):
    help = 'Create product categories for the marketplace'

    def handle(self, *args, **options):
        categories = [
            # Electronics
            "Électronique",
            "Téléphones & Accessoires",
            "Informatique",
            "TV & Audio",
            "Photo & Vidéo",
            "Jeux Vidéo",
            
            # Fashion
            "Mode Homme",
            "Mode Femme",
            "Mode Enfant",
            "Chaussures",
            "Montres & Bijoux",
            "Sacs & Bagagerie",
            
            # Home & Living
            "Maison & Décoration",
            "Cuisine & Maison",
            "Jardin & Extérieur",
            "Bricolage",
            "Literie & Linge",
            
            # Health & Beauty
            "Beauté & Soins",
            "Parfums",
            "Santé & Bien-être",
            
            # Sports & Outdoors
            "Sport & Fitness",
            "Vélos & Mobilité",
            "Camping & Randonnée",
            
            # Kids & Baby
            "Jouets & Jeux",
            "Bébé & Puériculture",
            
            # Books & Media
            "Livres",
            "Musique & Films",
            
            # Auto & Moto
            "Auto & Moto",
            
            # Food & Drinks
            "Alimentation",
            "Boissons",
            
            # Services & Others
            "Animaux",
            "Fournitures Bureau",
        ]
        
        created_count = 0
        for name in categories:
            category, created = Category.objects.get_or_create(name=name)
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ {name}')
            else:
                self.stdout.write(f'  - {name} (exists)')
        
        self.stdout.write(self.style.SUCCESS(f'\n{created_count} categories created!'))