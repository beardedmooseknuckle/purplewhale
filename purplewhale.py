import click

@click.group()
def cli():
  pass

@cli.group('chatbot', short_help='Manage the Twitch chatbot')
def cmd_chatbot():
  pass

@cmd_chatbot.command('start')
def chatbot_start():
  from chatbot import create_app
  app = create_app()
  app.run()

@cmd_chatbot.command('stop')
def chatbot_stop():
  pass

@cmd_chatbot.command('restart')
def chatbot_restart():
  pass

@cli.group('setup', short_help='Commands to initialize an installation')
def cmd_setup():
  pass

@cmd_setup.command('instance', short_help='Quality of life helper to create a default instance folder for this PurpleWhale installation')
@click.option('--force', is_flag=True, help='Force populating an existing instance folder (files WILL be overwritten)')
def setup_instance(force):
  import os, shutil
  
  instance_path = os.path.join(os.getcwd(), 'instance/')
  if os.path.exists(instance_path):
    if not force:
      print('Instance folder already exists. To force population of default files, use the `--force` switch.')
      return True
  else:
    # Make sure our instance folder exists
    # @todo change the umask to restrict viewership?
    os.mkdir(instance_path)
    print('Instance folder created.')
  
  docs_instance_path = os.path.join(os.getcwd(), 'docs', 'instance')
  instance_files = ('api.py.example', 'chatbot.py.example', 'frontend.py.example')
  for file in instance_files:
    file_path = os.path.join(docs_instance_path, file)
    shutil.copy(file_path, instance_path)
  
  print('Instance folder populated.')
  print('Next, you should update the files with your installation settings and remove the `.example` extension.')


@cmd_setup.command('frontend_db', short_help='Create database tables for the frontend Flask app')
def setup_frontend_db():
  from webapp.frontend import init_db
  init_db()
  print('Frontend database tables initiated.')

@cmd_setup.command('chatbot_db', short_help='Create database tables for the Chatbot module')
def setup_chatbot_db():
  from chatbot import init_db
  init_db()
  print('Chatbot database tables initiated.')

@cmd_setup.command('gunicorn', short_help='Generate a Gunicorn service file for the Flask apps')
@click.option('--user', prompt='User for this service', default='www-data')
@click.option('--group', prompt='Group for this service', default='www-data')
def setup_gunicorn(user, group):
  from jinja2 import Template
  import os, subprocess
  
  # Create a Jinja2 Template object from PurpleWhale's service file template
  purplewhale_cwd = os.getcwd()
  template_webapp_service_file = os.path.join(purplewhale_cwd, 'docs', 'gunicorn', 'purplewhale-webapp.service')
  with open(template_webapp_service_file) as f1:
    template_data = f1.read()
    template = Template(template_data)

  # Prepare the values of the template variables in the service file template
  pipenv_venv_folder = subprocess.run(['pipenv', '--venv'], capture_output=True, encoding='utf-8')
  template_values = {
                      'service_user': user,
                      'service_group': group,
                      'purplewhale_path': purplewhale_cwd,
                      'purplewhale_venv_path': pipenv_venv_folder.stdout.strip('\n')
                      }
  
  # Write a service file for this specific PurpleWhale instance
  instance_webapp_service_file = os.path.join(os.getcwd(), 'instance', 'purplewhale-webapp.service')
  with open(instance_webapp_service_file, 'w') as f2:
    f2.write(template.render(**template_values))
  
  # @todo improve these instructions
  print(f'Gunicorn service file created: {instance_webapp_service_file}')
  print('1. Copy/move the file to the `/etc/systemd/system` folder and use the `systemctl` command to start it.')
  
@cmd_setup.command('nginx', short_help='Generate an nginx site file to proxy to Gunicorn')
@click.option('--domains', prompt='Domains for this site (space-separated, example: purplewhale.org www.purplewhale.org)')
def setup_gunicorn(domains):
  from jinja2 import Template
  import os, subprocess
  
  # Create a Jinja2 Template object from PurpleWhale's service file template
  purplewhale_cwd = os.getcwd()
  template_nginx_site_file = os.path.join(purplewhale_cwd, 'docs', 'nginx', 'purplewhale-site')
  with open(template_nginx_site_file) as f1:
    template_data = f1.read()
    template = Template(template_data)

  # Prepare the values of the template variables in the service file template
  template_values = { 
                      'domains': domains,
                      'purplewhale_path': purplewhale_cwd
                    }
  
  # Write a service file for this specific PurpleWhale instance
  instance_nginx_site_file = os.path.join(os.getcwd(), 'instance', 'purplewhale-site')
  with open(instance_nginx_site_file, 'w') as f2:
    f2.write(template.render(**template_values))
  
  # @todo improve these instructions
  print(f'nginx site file created: {instance_nginx_site_file}')
  print('1. Copy/move the file to the `/etc/nginx/sites-available/` folder with a desired filename and symlink the file to `/etc/nginx/sites-enabled/`.')
  print('2. Test for syntax errors: sudo nginx -t')
  print('3. If no issues, restart nginx: sudo systemctl restart nginx')
  print('4. Recommended to secure (https) your site using `certbot` (Let\'s Encrypt!)')

@cli.group('utils', short_help='Quality of life utilities to help with configuration')
def cmd_utils():
  pass

@cmd_utils.command('secret_key', short_help='Generate a secret key for Flask using Python\'s secrets module.')
@click.option('--length', default=16, help='Length of the secret key (default: 16)')
def utils_secret_key(length):
  import secrets
  print(secrets.token_urlsafe(length))

if __name__ == "__main__":
  cli()