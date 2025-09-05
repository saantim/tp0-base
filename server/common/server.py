import socket
import logging
import signal
import sys
import time

from .messages import MessageParser, AckMsg, WinnersMsg
import threading
from threading import Condition

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
        self.lock = threading.RLock()
        self.threads_lock = threading.Lock()
        self.winners_condition = Condition(self.lock)
        self.running = True
        self.threads_running = threading.Event()
        self.threads = []
        self.cleaner = None

    def handle_sigterm(self, signum, frame):
        """Handle SIGTERM signal for graceful shutdown.
        
        This method is called when a SIGTERM signal is received. It initiates
        a graceful shutdown of the server by closing the server socket and
        notifying all waiting threads.

        """
        logging.info("action: graceful_shutdown | result: in_progress")
        try:
            self._server_socket.close()
        except Exception:
            pass
        logging.info("action: graceful_shutdown | result: success")
        self.running = False
        self.threads_running.set()
        if self.cleaner: self.cleaner.join()
        self._cleanup_threads()

    def run(self):
        """Run the main server loop.
        
        Listens for new client connections and spawns a new thread for each one.
        Handles both SIGTERM and KeyboardInterrupt for graceful shutdown.
        
        The server will continue running until a shutdown signal is received or
        a keyboard interrupt occurs.
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        signal.signal(signal.SIGTERM, self.handle_sigterm)
        self.cleaner = threading.Thread(target=self._deamon_clenup, daemon=True)
        self.cleaner.start()
        try:
            while self.running:
                client_sock = self.__accept_new_connection()
                if client_sock:
                    with self.threads_lock:
                        client_thread = threading.Thread(
                            target=self.__handle_client_connection, 
                            args=(client_sock,),
                        )
                        self.threads.append(client_thread)
                    client_thread.start()
        except KeyboardInterrupt:
            logging.info("action: graceful_shutdown | result: in_progress")
            self._server_socket.close()
            if self.cleaner: self.cleaner.join()
            logging.info("action: graceful_shutdown | result: success")

    def _deamon_clenup(self):
        while not self.threads_running.wait(timeout=5):
            self._cleanup_threads()

    def _cleanup_threads(self):
        """
        Check the list of threads and remove those that have already finished execution.
        """
        with self.threads_lock:
            threads_to_clean = [t for t in self.threads if not t.is_alive()]
            
        for thread in threads_to_clean:
            thread.join()
            
        if threads_to_clean:
            with self.threads_lock:
                self.threads = [t for t in self.threads if t.is_alive()]
                logging.debug(f"Cleaned up {len(threads_to_clean)} finished threads")

    def __handle_client_connection(self, client_sock):
        """Handle client connection and process incoming messages.
        
        Continuously receives and processes messages from the client until the
        connection is closed or an error occurs. The client socket is always
        closed after processing, regardless of success or failure.
        
        Args:
            client_sock: The client socket to communicate with.
            
        Returns:
            int: 0 if the connection was handled successfully, 1 if an error occurred.
        """
        try:
            recv_bets = 0
            error_occurred = False
            while not self.threads_running.is_set():
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
        with self.lock:
            utils.store_bets(bets)
        response = AckMsg(True)
        client_sock.sendall(response.to_bytes())
        return recv_bets

    def handle_get_winners(self, client_sock, msg):
        """Handle a request for winners from a client.

        Retrieves the list of winners for the client's agency and sends it back.
        If the winners haven't been processed yet, this method will block until
        they are available.

        """
        with self.lock:
            while not self.winners_processed:
                self.winners_condition.wait()
            agency_id = msg.get_parser().get_agency_id()
            winners = self.winners.get(agency_id, [])
            winners_msg = WinnersMsg(winners)
            client_sock.sendall(winners_msg.to_bytes())

    def handle_finished_batch(self, client_sock, recv_bets):
        """Handle notification that a client has finished sending bets.
        
        Updates the count of agencies that have finished sending bets. If all
        agencies have finished, it triggers the winner determination process.
        
        Note:
            This method is thread-safe and may notify waiting threads when all
            agencies have reported in.
        """
        logging.info(f"action: apuesta_recibida | result: success | cantidad: {recv_bets}")
        with self.lock:
            self.received_agencies += 1
            if self.received_agencies == self._quantity_agencies:
                logging.info("action: sorteo | result: success")
                with self.winners_condition:
                    self.process_bets()
                    self.winners_processed = True
                    self.winners_condition.notify_all()
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