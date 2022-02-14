from os import environ

if environ.get('APP_ENV') == 'docker':
    node_api_key = environ.get('NODE_API_KEY', 'nodeapikey')
    node_ip = environ.get('NODEIP', 'vsystems')
    block_time = int(environ.get('BLOCK_TIME', '4'))

else:
    node_api_key = "5&!aJ#gyu2i#"
    node_ip = "gabija.vos.systems"
    block_time = 4
