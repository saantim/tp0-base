package common

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"os/signal"
	"strconv"
	"syscall"
	"time"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/common/messages"
	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/common/model"
	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// CreateClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Criticalf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
	}
	c.conn = conn
	return nil
}

// StartClientLoop Send bet messages to the client and handles the server's ack
func (c *Client) StartClientLoop() {
	c.createClientSocket()
	defer c.conn.Close()
	handleSigterm(c)

	bet := buildBetFromEnvVars()
	betMsg := messages.BetMsg{Bet: bet}
	err := writeAll(c.conn, betMsg.ToBytes())

	if err != nil {
		log.Errorf("There was an error sending a message")
		return
	}

	msg, err := readExactBytes(bufio.NewReader(c.conn), messages.AckMsgLen)

	ack := messages.BuildAckMsg(msg)
	if ack.SuccessResult() && err == nil {
		log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v",
			bet.ID,
			bet.BetNum,
		)
	}
}

// buildBetFromEnvVars creates a Bet struct by reading values from environment variables.
func buildBetFromEnvVars() model.Bet {
	agency, _ := strconv.Atoi(os.Getenv("CLI_ID"))
	name := os.Getenv("NOMBRE")
	lastName := os.Getenv("APELLIDO")
	id, _ := strconv.Atoi(os.Getenv("DOCUMENTO"))
	birthDate := os.Getenv("NACIMIENTO")
	number, _ := strconv.Atoi(os.Getenv("NUMERO"))
	return model.Bet{
		Agency:   uint8(agency),
		Name:     name,
		LastName: lastName,
		ID:       uint32(id),
		BirthDay: birthDate,
		BetNum:   uint32(number),
	}
}

// handleSigterm handles SIGTERM signal for graceful shutdown.
// Closes active connection and exits with status 0.
// c: Client instance to close connection for
func handleSigterm(c *Client) {
	sigChannel := make(chan os.Signal, 1)
	signal.Notify(sigChannel, syscall.SIGTERM)

	go func() {
		_ = <-sigChannel
		log.Infof("Sigterm received - Starting gracefully shut down")
		c.conn.Close()
		log.Infof("Gracefully shutdown done!")
		os.Exit(0)
	}()
}

// writeAll writes the complete data to the connection to avoid short writes
func writeAll(conn net.Conn, data []byte) error {
	totalWritten := 0
	for totalWritten < len(data) {
		n, err := conn.Write(data[totalWritten:])
		if err != nil {
			return fmt.Errorf("error writing to connection: %v", err)
		}
		totalWritten += n
	}
	return nil
}

// readExactBytes reads exactly n bytes from the reader to avoid short reads
func readExactBytes(reader *bufio.Reader, n int) ([]byte, error) {
	buf := make([]byte, n)
	read := 0

	for read < n {
		count, err := reader.Read(buf[read:])
		if err != nil {
			return nil, err
		}
		read += count
	}

	return buf, nil
}
