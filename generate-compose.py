import sys

# YAML template for the docker-compose file header
HEADER = """
name: tp0
services:
"""

# YAML template for the server service configuration
SERVER = """
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini

"""

# YAML template for the network configuration
NETWORK = """
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""

# YAML template for client services (uses string formatting for client ID)
CLIENT = """
  client{0}:
    container_name: client{0}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={0}
      - NOMBRE=Pepito
      - APELLIDO=Gomez
      - DOCUMENTO=12345678
      - NACIMIENTO=1990-01-01
      - NUMERO=7574
    networks:
      - testing_net
    depends_on:
      - server
    volumes:
      - ./client/config.yaml:/config.yaml
"""

def parse_args(args):
    """
    Parse and validate command line arguments.

    Args:
        args (list): Command line arguments [output_file, client_count]

    Returns:
        tuple: (output_file_path, number_of_clients)
    """
    if len(args) != 2:
        print("Error: wrong quantity of arguments")
        print("Usage: python generate-compose.py <output_file.yaml> <number_of_clients>")
        sys.exit(1)

    dest_path = args[0]
    quantity = args[1]

    if dest_path.split(".")[-1] != 'yaml':
        print("Error: validate file name and extension")
        sys.exit(1)

    if not quantity.isdigit():
        print("Error: quantity of clients must be a number")
        sys.exit(1)

    return dest_path, int(quantity)

def main():
    """
    Main function that generates the docker-compose configuration file.
    
    The function:
    1. Parses command line arguments
    2. Generates the docker-compose YAML content
    3. Writes the configuration to the specified output file
    """
    args = sys.argv[1:]
    path, quantity = parse_args(args)

    with open(path, "w") as f:
        script = HEADER + SERVER
        for i in range(1, quantity + 1):
            script += CLIENT.format(i)
        script += NETWORK
        f.write(script)

if __name__ == "__main__":
    main()