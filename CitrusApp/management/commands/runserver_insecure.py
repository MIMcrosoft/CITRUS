from django.contrib.staticfiles.management.commands.runserver import (
    Command as RunserverCommand,
)


class Command(RunserverCommand):
    help = "runserver avec --insecure activé (sert les fichiers statiques même si DEBUG=False)"

    def handle(self, *args, **options):
        options["insecure_serving"] = True
        super().handle(*args, **options)