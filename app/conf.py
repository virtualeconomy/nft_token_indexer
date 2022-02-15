from os import environ
import yaml

if environ.get('APP_ENV') == 'docker':
    node_api_key = environ.get('NODE_API_KEY', 'nodeapikey')
    node_ip = environ.get('NODEIP', 'vsystems')
    node_port = environ.get('NODE_PORT', '9924')
    block_time = int(environ.get('BLOCK_TIME', '4'))
    db_user = environ.get('DB_USER')
    db_pass = environ.get('DB_PASS')
    db_ip = environ.get('DB_IP')

else:
    node_api_key = "5&!aJ#gyu2i#"
    node_ip = "gabija.vos.systems"
    node_port="9924"
    block_time = 4
    db_user = "postgres"
    db_pass = "postgres"
    db_ip = "0.0.0.0"


with open("conf.yaml", "r") as f:
    try:
        config = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(exc)


contract_ids = list(config.keys())
