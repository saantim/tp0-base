import sys

HEADER = """
name: tp0
services:
"""

SERVER = """
  server:
    container_name: server
    image: server:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - LOGGING_LEVEL=DEBUG
    networks:
      - testing_net
    volumes:
      - ./server/config.ini:/config.ini

"""

NETWORK = """
networks:
  testing_net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""

CLIENT = """
  client{0}:
    container_name: client{0}
    image: client:latest
    entrypoint: /client
    environment:
      - CLI_ID={0}
      - CLI_LOG_LEVEL=DEBUG
    networks:
      - testing_net
    depends_on:
      - server
    volumes:
      - ./client/config.yaml:/config.yaml
"""

def parse_args(args):
    if len(args) != 2:
        print("Error: wrong quantity of arguments")
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