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
        self.running = True

    def handle_sigterm(self, signum, frame):
        """Handle SIGTERM signal for graceful shutdown.
            modify the running flag to False
        """
        logging.info("action: graceful_shutdown | result: in_progress")
        try:
            self._server_socket.close()
        except Exception:
            pass
        logging.info("action: graceful_shutdown | result: success")
        self.running = False

    def run(self):
        """
        Main server loop that accepts and handles client connections.

        Listens for new connections and processes each client in sequence.
        Handles SIGTERM and KeyboardInterrupt for graceful shutdown.
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        try:
            while self.running:
                client_sock = self.__accept_new_connection()
                if client_sock:
                    self.__handle_client_connection(client_sock)
        except KeyboardInterrupt:
            logging.info("action: graceful_shutdown | result: in_progress")
            self._server_socket.close()
            logging.info("action: graceful_shutdown | result: success")

    def __handle_client_connection(self, client_sock):
        """
        Handle client connection: receive bets and send acknowledgments.
        The client socket is always closed after processing, regardless of success or failure.
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

        If the server is not running, returns None
        """

        # Connection arrived
        try:
            logging.info('action: accept_connections | result: in_progress')
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        except OSError as e:
            if not self.running:
                return None
        return c

def recv_bet(client_sock):
    """Receive and parse a bet message from a client.
    
    Args:
        client_sock: The client socket to receive data from.
        
    Returns:
        Bet: The parsed bet message if successful, None otherwise.
    """
    header = client_sock.recv(MessageParser.HEADER_SIZE, socket.MSG_WAITALL)
    if not header:
        logging.error("action: receive_message | result: fail | error: no_header")
        return None
    to_read = MessageParser.expected_bytes(header)

    msg = client_sock.recv(to_read, socket.MSG_WAITALL)
    if len(msg) != to_read:
        logging.error(
            f'action: receive_message | result: fail | error: incomplete_message | received: {len(msg)} bytes')
        return None

    return MessageParser(header, msg).parse()