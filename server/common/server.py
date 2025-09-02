import socket
import logging
import signal
import sys
from .messages import MessageParser, AckMsg
from . import utils
class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

    def handle_sigterm(self, signum, frame):
        logging.info("action: graceful_shutdown | result: in_progress")
        self._server_socket.close()
        logging.info("action: graceful_shutdown | result: success")
        sys.exit(0)

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        try:
            while True:
                client_sock = self.__accept_new_connection()
                self.__handle_client_connection(client_sock)
        except KeyboardInterrupt:
            logging.info("action: graceful_shutdown | result: in_progress")
            self._server_socket.close()
            logging.info("action: graceful_shutdown | result: success")

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            bet = recv_bet(client_sock)
            if not bet:
                logging.error("action: receive_message | result: fail | error: invalid_bet_data")
                return

            utils.store_bets([bet])
            logging.info(f"action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}")

            response = AckMsg(True)
            client_sock.sendall(response.to_bytes())

        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c

def recv_bet(client_sock):
    msg = client_sock.recv(84, socket.MSG_WAITALL)
    if len(msg) != 84:
        logging.error(
            f'action: receive_message | result: fail | error: incomplete_message | received: {len(msg)} bytes')
        return None

    return MessageParser(msg).parse()