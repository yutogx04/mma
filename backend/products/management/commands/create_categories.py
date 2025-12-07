from django.core.management.base import BaseCommand
from products.models import Category


class Command(BaseCommand):
    help = 'Create product categories for the marketplace'

    def handle(self, *args, **options):
        categories = [
            "Électronique",
            "Téléphones & Accessoires",
            "Informatique",
            "TV & Audio",
            "Photo & Vidéo",
            "Jeux Vidéo",
            
            "Mode Homme",
            "Mode Femme",
            "Mode Enfant",
            "Chaussures",
            "Montres & Bijoux",
            "Sacs & Bagagerie",
            
            "Maison & Décoration",
            "Cuisine & Maison",
            "Jardin & Extérieur",
            "Bricolage",
            "Literie & Linge",
            
            "Beauté & Soins",
            "Parfums",
            "Santé & Bien-être",
            
            "Sport & Fitness",
            "Vélos & Mobilité",
            "Camping & Randonnée",
            
            "Jouets & Jeux",
            "Bébé & Puériculture",
            
            "Livres",
            "Musique & Films",
            
            "Auto & Moto",
            
            "Alimentation",
            "Boissons",
            
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