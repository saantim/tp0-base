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
        self._quantity_agencies = quantity_agencies
        self.received_agencies = 0
        self.winners_processed = False
        self.winners = {}


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
            recv_bets = 0
            error_occurred = False
            while True:
                msg: MessageParser
                msg, error = recv_msg(client_sock)
                if error: error_occurred = True
                if not msg:
                    break

                if msg.is_bet_msg():
                    bets_parser = msg.get_parser()
                    bets = bets_parser.parse()

                    recv_bets += len(bets)
                    utils.store_bets(bets)

                    response = AckMsg(True)
                    client_sock.sendall(response.to_bytes())

                if msg.is_finish_batch_msg():
                    logging.info(f"action: finish_batch | result: in_progress | agency_id: {msg.get_parser().get_agency_id()}")
                    self.received_agencies += 1
                    logging.info(f"Agencias registradas {self.received_agencies}, Total esperado: {self._quantity_agencies}")
                    if self.received_agencies == self._quantity_agencies:
                        self.process_bets()
                        self.winners_processed = True
                    response = AckMsg(True)
                    client_sock.sendall(response.to_bytes())

                if msg.is_ask_winners_msg():
                    logging.info(f"action: ask_winners | result: in_progress | agency_id: {msg.get_parser().get_agency_id()}")
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
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c

    def process_bets(self):
        for bet in utils.load_bets():
            if utils.has_won(bet):
                if not self.winners.get(bet.agency_id):
                    self.winners[bet.agency_id] = []
                self.winners[bet.agency_id].append(bet)

def recv_msg(client_sock):
    header = client_sock.recv(MessageParser.HEADER_SIZE, socket.MSG_WAITALL)
    if not header:
        return None, False
    to_read = MessageParser.expected_bytes(header)
    msg = client_sock.recv(to_read, socket.MSG_WAITALL)
    if len(msg) != to_read:
        return None, True
    return MessageParser(header, msg), False