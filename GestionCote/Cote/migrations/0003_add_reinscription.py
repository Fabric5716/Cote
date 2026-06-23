# Cote/migrations/0003_add_reinscription.py
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('Cote', '0002_alter_classe_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='Reinscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('est_redoublant', models.BooleanField(default=False, verbose_name='Est redoublant')),
                ('date_reinscription', models.DateTimeField(auto_now_add=True, verbose_name='Date de réinscription')),
                ('est_validee', models.BooleanField(default=False, verbose_name='Est validée')),
                ('date_validation', models.DateTimeField(blank=True, null=True, verbose_name='Date de validation')),
                ('observations', models.TextField(blank=True, null=True, verbose_name='Observations')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('annee_scolaire', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Cote.anneescolaire', verbose_name='Année scolaire')),
                ('classe_ancienne', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='anciennes_reinscriptions', to='Cote.classe', verbose_name='Ancienne classe')),
                ('classe_nouvelle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nouvelles_reinscriptions', to='Cote.classe', verbose_name='Nouvelle classe')),
                ('eleve', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='Cote.eleve', verbose_name='Élève')),
                ('validee_par', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='Cote.utilisateur', verbose_name='Validée par')),
            ],
            options={
                'verbose_name': 'Réinscription',
                'verbose_name_plural': 'Réinscriptions',
                'ordering': ['-date_reinscription'],
                'unique_together': {('eleve', 'annee_scolaire')},
            },
        ),
    ]