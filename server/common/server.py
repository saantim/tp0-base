import socket
import logging
import signal
import sys
from .messages import MessageParser, AckMsg, WinnersMsg
from . import utils
class Server:
    def __init__(self, port, listen_backlog, quantity_agencies):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self._quantity_agencies = int(quantity_agencies)
        self.received_agencies = 0
        self.winners_processed = False
        self.winners = {}
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
            recv_bets = 0
            error_occurred = False
            while self.running:
                msg: MessageParser
                msg, error = recv_msg(client_sock)
                if error: error_occurred = True
                if not msg:
                    break

                if msg.is_bet_msg():
                    recv_bets = self.handle_new_bets(client_sock, msg, recv_bets)

                if msg.is_finish_batch_msg():
                    self.handle_finished_batch(client_sock, recv_bets)

                if msg.is_ask_winners_msg():
                    self.handle_get_winners(client_sock, msg)

            if error_occurred:
                return 1
            return 0

        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
            return 1
        finally:
            logging.info(f"Closing client socket {client_sock.getpeername()}")
            client_sock.close()

    def handle_new_bets(self, client_sock, msg, recv_bets):
        """
        Handle new bets received from a client.

        """
        bets_parser = msg.get_parser()
        bets = bets_parser.parse()
        recv_bets += len(bets)
        utils.store_bets(bets)
        response = AckMsg(True)
        client_sock.sendall(response.to_bytes())
        return recv_bets

    def handle_get_winners(self, client_sock, msg):
        """
        Handle request for winners from a client.
        """
        if self.winners_processed:
            agency_id = msg.get_parser().get_agency_id()
            winners = self.winners.get(agency_id)
            if not winners:
                winners = []
            winners_msg = WinnersMsg(winners)
            client_sock.sendall(winners_msg.to_bytes())
        else:
            response = AckMsg(True)
            client_sock.sendall(response.to_bytes())

    def handle_finished_batch(self, client_sock, recv_bets):
        """ Handle finished batch of bets from a client. """
        logging.info(f"action: apuesta_recibida | result: success | cantidad: {recv_bets}")
        self.received_agencies += 1
        if self.received_agencies == self._quantity_agencies:
            logging.info("action: sorteo | result: success")
            self.process_bets()
            self.winners_processed = True
        response = AckMsg(True)
        client_sock.sendall(response.to_bytes())

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

    def process_bets(self):
        for bet in utils.load_bets():
            if utils.has_won(bet):
                if not self.winners.get(bet.agency):
                    self.winners[bet.agency] = []
                self.winners[bet.agency].append(bet.document)

def recv_msg(client_sock):
    """Receive a message from a client.
    
    Args:
        client_sock: The client socket to receive data from.
        
    Returns:
        Bet: returns the message parser.
    """
    header = client_sock.recv(MessageParser.HEADER_SIZE, socket.MSG_WAITALL)
    if not header:
        return None, False
    to_read = MessageParser.expected_bytes(header)
    msg = client_sock.recv(to_read, socket.MSG_WAITALL)
    if len(msg) != to_read:
        return None, True
    return MessageParser(header, msg), False