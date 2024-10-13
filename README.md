# Useful commands

cd Desktop/djangodevelopment
source bin/activate

watchmedo shell-command --patterns="*.css;*.js;*.html" --command="python manage.py collectstatic --noinput" --recursive static