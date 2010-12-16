import django.template
if not django.template.libraries.get('jdatetime.filters', None):
    django.template.add_to_builtins('jdatetime.filters')
