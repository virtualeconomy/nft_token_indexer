from os import environ
import yaml

if environ.get('APP_ENV') == 'docker':
    node_api_key = environ.get('NODE_API_KEY', 'nodeapikey')
    node_ip = environ.get('NODEIP', 'vsystems')
    block_time = int(environ.get('BLOCK_TIME', '4'))

else:
    node_api_key = "5&!aJ#gyu2i#"
    node_ip = "gabija.vos.systems"
    block_time = 4


with open("conf.yaml", "r") as f:
    try:
        config = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(exc)
