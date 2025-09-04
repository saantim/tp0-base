package common

import (
	"bufio"
	"fmt"
	"net"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"

	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/common/messages"
	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/common/model"
	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID             string
	ServerAddress  string
	LoopAmount     int
	LoopPeriod     time.Duration
	MaxBatchAmount int
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

func (c *Client) StartClient() {
	c.createClientSocket()
	defer c.conn.Close()
	handleSigterm(c)

	filename := fmt.Sprintf("/data/agency-%v.csv", c.config.ID)
	file, err := os.Open(filename)
	if err != nil {
		log.Errorf("There was an error opening file agency-%v", c.config.ID)
		return
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	var bets []model.Bet
	errorSending := false
	for scanner.Scan() {
		bet, _ := parseCsvLine(scanner, c.config)
		bets = append(bets, bet)

		if len(bets) >= c.config.MaxBatchAmount {
			if err := c.sendBatch(bets); err != nil {
				log.Errorf("Error sending batch: %v", err)
				return
			}
			bets = []model.Bet{}

			msg, err := readExactBytes(bufio.NewReader(c.conn), messages.AckMsgLen)
			ack := messages.BuildAckMsg(msg)
			if !ack.SuccessResult() || err != nil {
				errorSending = true
			}
		}

		time.Sleep(c.config.LoopPeriod)
	}
	if len(bets) > 0 {
		if err := c.sendBatch(bets); err != nil {
			errorSending = true
		}
	}

	msg, err := readExactBytes(bufio.NewReader(c.conn), messages.AckMsgLen)

	ack := messages.BuildAckMsg(msg)
	if !ack.SuccessResult() || err != nil {
		errorSending = true
	}
	if errorSending {
		log.Errorf("action: sending_batch | result: fail | error")
	}
}

func parseCsvLine(scanner *bufio.Scanner, config ClientConfig) (model.Bet, error) {
	line := strings.TrimSpace(scanner.Text())
	if line == "" {
		return model.Bet{}, fmt.Errorf("EmptyLine")
	}
	fields := strings.Split(line, ",")
	if len(fields) < 5 {
		return model.Bet{}, fmt.Errorf("line with wrong format")
	}

	id, err := strconv.Atoi(strings.TrimSpace(fields[2]))
	if err != nil {
		return model.Bet{}, fmt.Errorf("line with wrong id")
	}

	betNum, err := strconv.Atoi(strings.TrimSpace(fields[4]))
	if err != nil {
		return model.Bet{}, fmt.Errorf("line with wrong bet number")
	}

	agencyId, _ := strconv.Atoi(config.ID)
	return model.Bet{
		Agency:   uint8(agencyId),
		ID:       uint32(id),
		Name:     strings.TrimSpace(fields[0]),
		LastName: strings.TrimSpace(fields[1]),
		BirthDay: strings.TrimSpace(fields[3]),
		BetNum:   uint32(betNum),
	}, nil
}

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

func writeAll(conn net.Conn, data []byte) error {
	totalWritten := 0
	for totalWritten < len(data) {
		n, err := conn.Write(data[totalWritten:])
		if err != nil {
			log.Errorf("There was an error trying to write to server %v", err)
			return fmt.Errorf("error writing to connection: %v", err)
		}
		totalWritten += n
	}
	return nil
}

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

func (c *Client) sendBatch(bets []model.Bet) error {
	betBatch := messages.BetBatchMsg{Bets: bets}
	if err := writeAll(c.conn, betBatch.ToBytes()); err != nil {
		return fmt.Errorf("error sending batch: %v", err)
	}
	return nil
}
