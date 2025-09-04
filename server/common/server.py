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
        logging.info("action: graceful_shutdown | result: in_progress")
        try:
            self._server_socket.close()
        except Exception:
            pass
        logging.info("action: graceful_shutdown | result: success")
        self.running = False

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
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            recv_bets = 0
            error_occurred = False
            while self.running:
                bets, error = recv_bet(client_sock)
                if error: error_occurred = True
                if not bets:
                    break

                recv_bets += len(bets)
                utils.store_bets(bets)

                response = AckMsg(True)
                client_sock.sendall(response.to_bytes())

            if error_occurred:
                logging.info(f"action: apuesta_recibida | result: fail | cantidad: ${recv_bets}")
                return 1
            logging.info(f"action: apuesta_recibida | result: success | cantidad: {recv_bets}")
            return 0

        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
            return 1
        finally:
            logging.info(f"Closing client socket {client_sock.getpeername()}")
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
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
    header = client_sock.recv(MessageParser.HEADER_SIZE, socket.MSG_WAITALL)
    if not header:
        return None, False
    to_read = MessageParser.expected_bytes(header)

    msg = client_sock.recv(to_read, socket.MSG_WAITALL)
    if len(msg) != to_read:
        return None, True
    return MessageParser(header, msg).parse(), False